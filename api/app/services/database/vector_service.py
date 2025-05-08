"""Vector operations service.

Core operations for vector storage, updates, and similarity search using pgvector.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, text

from app.services.database.models import Document, Chunk
from app.services.embeddings_service import EmbeddingService
from app.models.document_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector operations with PostgreSQL and pgvector."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """Initialize the vector service."""
        self.embedding_service = embedding_service or EmbeddingService()

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
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.

        Args:
            db: Database session
            query_text: Query text
            limit: Maximum number of results
            min_score: Minimum similarity score threshold
            filters: Optional filters to apply to the search

        Returns:
            List of search results with similarity scores
        """
        # Generate embedding for query
        query_embedding = (
            await self.embedding_service.generate_embeddings([query_text])
        )[0]

        # Build the query
        stmt = (
            select(
                Chunk,
                func.cosine_similarity(Chunk.embedding, query_embedding).label(
                    "similarity"
                ),
            )
            .where(Chunk.embedding.is_not(None))
            .order_by(func.cosine_similarity(Chunk.embedding, query_embedding).desc())
            .limit(limit)
        )

        # Add minimum score filter if provided
        if min_score is not None:
            stmt = stmt.where(
                func.cosine_similarity(Chunk.embedding, query_embedding) >= min_score
            )

        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if "->" in field:
                    # Handle JSON path expressions
                    stmt = stmt.where(text(f"{field} = :value").bindparams(value=value))
                else:
                    # Handle regular columns
                    stmt = stmt.where(getattr(Chunk, field) == value)

        # Execute query and format results
        results = db.execute(stmt).all()
        return [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "similarity_score": float(score),
            }
            for chunk, score in results
        ]


# Create a singleton instance
vector_service = VectorService()
