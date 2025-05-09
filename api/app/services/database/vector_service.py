"""Vector operations service.

Core operations for vector storage, updates, and similarity search using pgvector.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, text
import numpy as np

# Import proper pgvector adapter for psycopg v3
from pgvector.psycopg import register_vector

from app.services.database.models import Document, Chunk
from app.services.embeddings_service import EmbeddingService
from app.models.document_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector operations with PostgreSQL and pgvector."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """Initialize the vector service."""
        self.embedding_service = embedding_service or EmbeddingService()

    def _prepare_embedding_for_query(self, embedding):
        """Prepare embedding for use in pgvector queries."""
        # Make sure embedding is flat list of floats
        if isinstance(embedding, (list, tuple)):
            return list(embedding)
        # If numpy array, convert to list
        try:
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()
        except ImportError:
            pass
        # Return as is
        return embedding

    async def insert_document(
        self,
        db: Session,
        processed_document: ProcessedDocument,
    ) -> int:
        """Insert a processed document and its chunks into the database.

        Args:
            db: Database session
            processed_document: The processed document with chunks

        Returns:
            The document ID of the inserted document
        """
        logger.info(
            f"Inserting document: {processed_document.document_id} with {processed_document.total_chunks} chunks"
        )

        # Handle document_id - support both string and integer IDs
        input_doc_id = None
        try:
            # Try to convert the document_id to an integer if it's a string with numeric content
            if (
                processed_document.document_id
                and processed_document.document_id.isdigit()
            ):
                input_doc_id = int(processed_document.document_id)
                logger.info(
                    f"Converting string document_id '{processed_document.document_id}' to integer: {input_doc_id}"
                )
        except (ValueError, AttributeError) as e:
            # If conversion fails, log it but proceed with auto-generated ID
            logger.warning(
                f"Could not convert document_id to integer: {e}. Will use auto-generated ID."
            )
            input_doc_id = None

        # Create document record
        db_document = Document(
            document_id=input_doc_id,  # Will be None if conversion failed, allowing auto-generation
            document_text=" ".join([chunk.text for chunk in processed_document.chunks]),
            document_source=processed_document.metadata.get("source", "upload"),
            document_file_path=processed_document.original_filename,
        )

        try:
            db.add(db_document)
            db.flush()  # Flush to get the document_id

            document_id = db_document.document_id
            logger.info(f"Document inserted with ID: {document_id}")

            # Generate embeddings for all chunks
            chunk_texts = [chunk.text for chunk in processed_document.chunks]
            embeddings = await self.embedding_service.generate_embeddings(chunk_texts)

            # Create chunks with embeddings
            for i, (chunk, embedding) in enumerate(
                zip(processed_document.chunks, embeddings, strict=False)
            ):
                db_chunk = Chunk(
                    content=chunk.text,
                    document_id=document_id,
                    chunk_sequence_in_document=i,
                    embedding=embedding,
                )
                db.add(db_chunk)

            db.commit()
            return document_id
        except Exception as e:
            db.rollback()
            logger.error(f"Error inserting document: {e}")
            raise

    async def store_document_vectors(
        self,
        db: Session,
        document_id: int,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        """Store document chunks with vectors.

        Args:
            db: Database session
            document_id: ID of the parent document
            texts: List of text chunks to embed
            metadata: Optional list of metadata for each chunk

        Returns:
            List of created chunk IDs
        """
        # Generate embeddings for all texts
        embeddings = await self.embedding_service.generate_embeddings(texts)

        # Create chunks with embeddings
        chunk_ids = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings, strict=False)):
            chunk_metadata = metadata[i] if metadata and i < len(metadata) else None

            # Create document chunk with embedding
            db_chunk = Chunk(
                document_id=document_id,
                chunk_sequence_in_document=i,
                content=text,
                embedding=embedding,
            )
            db.add(db_chunk)
            db.flush()
            chunk_ids.append(db_chunk.chunk_id)

        db.commit()
        return chunk_ids

    async def update_vectors(
        self, db: Session, chunk_ids: List[int], texts: Optional[List[str]] = None
    ) -> int:
        """Update embeddings for existing chunks.

        Args:
            db: Database session
            chunk_ids: List of chunk IDs to update
            texts: Optional list of texts (if content is also changing)

        Returns:
            Number of chunks updated
        """
        if not chunk_ids:
            return 0

        updated_count = 0

        # If new texts are provided, update content and embeddings
        if texts and len(texts) == len(chunk_ids):
            # Generate new embeddings
            embeddings = await self.embedding_service.generate_embeddings(texts)

            # Update each chunk
            for chunk_id, text, embedding in zip(
                chunk_ids, texts, embeddings, strict=False
            ):
                stmt = (
                    update(Chunk)
                    .where(Chunk.chunk_id == chunk_id)
                    .values(content=text, embedding=embedding)
                )
                result = db.execute(stmt)
                updated_count += result.rowcount
        else:
            # Update only embeddings for existing content
            chunks = db.query(Chunk).filter(Chunk.chunk_id.in_(chunk_ids)).all()
            if chunks:
                texts = [chunk.content for chunk in chunks]
                embeddings = await self.embedding_service.generate_embeddings(texts)

                # Update embeddings
                for chunk, embedding in zip(chunks, embeddings, strict=False):
                    chunk.embedding = embedding
                    updated_count += 1

        db.commit()
        return updated_count

    async def vector_search(
        self,
        db: Session,
        query_text: str,
        limit: int = 5,
        min_score: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_document_metadata: bool = False,
        context_window: int = 0,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Search for similar documents using vector similarity.

        Args:
            db: Database session
            query_text: Query text
            limit: Maximum number of results
            min_score: Minimum similarity score threshold (defaults to None)
            filters: Optional filters to apply to the search, format:
                     {'field': value} or {'document_field': value} for document filters
            include_document_metadata: Whether to include document metadata in the response
            context_window: Number of chunks before and after the matching chunk to include

        Returns:
            List of matching chunks with similarity scores
        """
        try:
            # First generate an embedding for the query text
            embedding = await self.embedding_service.generate_embeddings([query_text])
            if not embedding or len(embedding) == 0:
                logger.error("Failed to generate embeddings for query text")
                return []

            # Get the first embedding (we only sent one text)
            query_embedding = embedding[0]

            # Prepare the vector embedding properly formatted for PostgreSQL
            # Print some debug info
            print(f"Original embedding type: {type(query_embedding)}")
            print(f"Original embedding structure: {type(query_embedding).__name__}")
            print(f"Embedding length: {len(query_embedding)}")

            # Transform embedding to proper format if needed
            query_embedding = self._prepare_embedding_for_query(query_embedding)

            # Print more debug info after transformation
            print(f"Final embedding type: {type(query_embedding)}")
            print(f"Final embedding length: {len(query_embedding)}")
            print(f"First few elements: {query_embedding[:5]}")

            # Format the embedding as a proper SQL array with square brackets
            vector_str = f"[{','.join(map(str, query_embedding))}]"

            # Use proper SQL with the vector cast that doesn't conflict with parameter binding
            sql = """
                SELECT
                    chunks.chunk_id,
                    chunks.content,
                    chunks.document_id,
                    chunks.chunk_sequence_in_document,
                    1 - (chunks.embedding <=> %s::vector) AS similarity
                FROM chunks
                WHERE chunks.embedding IS NOT NULL
                 AND 1 - (chunks.embedding <=> %s::vector) >= %s ORDER BY similarity DESC LIMIT %s
            """
            print(f"Executing SQL:\n{sql}")

            # Execute the query with positional parameters
            # Use raw execution to avoid SQLAlchemy parameter style conflicts
            conn = db.get_bind().raw_connection()
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        vector_str,
                        vector_str,
                        min_score if min_score is not None else 0.0,
                        limit,
                    ),
                )
                rows = cur.fetchall()

            # Process results...
            results = []
            for row in rows:
                chunk_id = row[0]
                content = row[1]
                document_id = row[2]
                chunk_seq = row[3]
                similarity = float(row[4])

                chunk_result = {
                    "chunk_id": chunk_id,
                    "content": content,
                    "document_id": document_id,
                    "chunk_sequence": chunk_seq,
                    "similarity": similarity,
                }

                results.append(chunk_result)

            # Handle context window if specified
            if context_window > 0 and results:
                return self._add_context_to_results(
                    db, results, context_window, include_document_metadata
                )
            elif include_document_metadata and results:
                return self._add_document_metadata_to_results(db, results)

            return results

        except Exception as e:
            logger.error(f"Error in vector_search: {e}")
            print(f"Vector search error: {e}")
            raise

    def _add_context_to_results(
        self, db, results, context_window, include_document_metadata
    ):
        """Add surrounding context chunks to search results."""
        enhanced_results = []

        for result in results:
            document_id = result["document_id"]
            chunk_sequence = result["chunk_sequence"]
            chunk_id = result["chunk_id"]

            # Calculate the range for context chunks
            start_seq = max(1, chunk_sequence - context_window)
            end_seq = chunk_sequence + context_window

            # Get context chunks
            context_sql = """
                SELECT chunk_id, content, chunk_sequence_in_document
                FROM chunks
                WHERE document_id = %s
                AND chunk_sequence_in_document BETWEEN %s AND %s
                AND chunk_id != %s
                ORDER BY chunk_sequence_in_document
            """

            # Get a raw connection
            conn = db.get_bind().raw_connection()
            with conn.cursor() as cur:
                cur.execute(context_sql, (document_id, start_seq, end_seq, chunk_id))
                context_results = cur.fetchall()

            context_chunks = [
                {"chunk_id": ctx[0], "content": ctx[1], "sequence": ctx[2]}
                for ctx in context_results
            ]

            # Add document metadata if requested
            document = {}
            if include_document_metadata:
                doc_sql = """
                    SELECT document_source, document_file_path, title, author, publication_date
                    FROM documents
                    WHERE document_id = %s
                """
                with db.get_bind().raw_connection().cursor() as cur:
                    cur.execute(doc_sql, (document_id,))
                    doc_result = cur.fetchone()

                if doc_result:
                    document = {
                        "document_id": document_id,
                        "document_source": doc_result[0],
                        "document_file_path": doc_result[1],
                        "title": doc_result[2],
                        "author": doc_result[3],
                        "publication_date": doc_result[4],
                    }
            else:
                document = {"document_id": document_id}

            # Format the enhanced result
            enhanced_result = {
                "chunk": {
                    "chunk_id": chunk_id,
                    "content": result["content"],
                    "sequence": chunk_sequence,
                },
                "document": document,
                "similarity": result["similarity"],
                "context_chunks": context_chunks,
            }

            enhanced_results.append(enhanced_result)

        return {"total_results": len(enhanced_results), "results": enhanced_results}

    def _add_document_metadata_to_results(self, db, results):
        """Add document metadata to search results without context."""
        enhanced_results = []

        for result in results:
            document_id = result["document_id"]

            # Get document metadata
            doc_sql = """
                SELECT document_source, document_file_path, title, author, publication_date
                FROM documents
                WHERE document_id = %s
            """
            with db.get_bind().raw_connection().cursor() as cur:
                cur.execute(doc_sql, (document_id,))
                doc_result = cur.fetchone()

            if doc_result:
                document = {
                    "document_id": document_id,
                    "document_source": doc_result[0],
                    "document_file_path": doc_result[1],
                    "title": doc_result[2],
                    "author": doc_result[3],
                    "publication_date": doc_result[4],
                }
            else:
                document = {"document_id": document_id}

            # Format the enhanced result
            enhanced_result = {
                "chunk_id": result["chunk_id"],
                "content": result["content"],
                "document": document,
                "similarity": result["similarity"],
            }

            enhanced_results.append(enhanced_result)

        return enhanced_results


# Create a singleton instance
vector_service = VectorService()
