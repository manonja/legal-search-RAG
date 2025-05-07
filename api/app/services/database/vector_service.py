"""Vector operations service.

Core operations for vector storage, updates, and similarity search using pgvector.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, text

from app.services.database.models import Document, DocumentChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector operations with PostgreSQL and pgvector."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """Initialize the vector service."""
        self.embedding_service = embedding_service or EmbeddingService()

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
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=text,
                metadata=chunk_metadata,
                embedding=embedding,
            )
            db.add(db_chunk)
            db.flush()
            chunk_ids.append(db_chunk.id)

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
                    update(DocumentChunk)
                    .where(DocumentChunk.id == chunk_id)
                    .values(content=text, embedding=embedding)
                )
                result = db.execute(stmt)
                updated_count += result.rowcount
        else:
            # Update only embeddings for existing content
            chunks = (
                db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
            )
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
                DocumentChunk,
                func.cosine_similarity(DocumentChunk.embedding, query_embedding).label(
                    "similarity"
                ),
            )
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(
                func.cosine_similarity(DocumentChunk.embedding, query_embedding).desc()
            )
            .limit(limit)
        )

        # Add minimum score filter if provided
        if min_score is not None:
            stmt = stmt.where(
                func.cosine_similarity(DocumentChunk.embedding, query_embedding)
                >= min_score
            )

        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if "->" in field:
                    # Handle JSON path expressions
                    stmt = stmt.where(text(f"{field} = :value").bindparams(value=value))
                else:
                    # Handle regular columns
                    stmt = stmt.where(getattr(DocumentChunk, field) == value)

        # Execute query and format results
        results = db.execute(stmt).all()
        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "similarity_score": float(score),
            }
            for chunk, score in results
        ]


# Create a singleton instance
vector_service = VectorService()
