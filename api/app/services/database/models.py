"""Database ORM models.

This module contains SQLAlchemy ORM models for document storage with vector embeddings.
"""

from sqlalchemy import Column, Index, Text, ForeignKey, VARCHAR, BigInteger
import pgvector.sqlalchemy as pgvector

from app.services.database.database import Base


class Document(Base):
    """Document ORM model for storing documents in the database."""

    __tablename__ = "documents"

    document_id = Column(BigInteger, primary_key=True, index=True)
    document_text = Column(Text, nullable=False)
    document_source = Column(VARCHAR(104), nullable=False)
    document_file_path = Column(VARCHAR(1024), nullable=True)


class Chunk(Base):
    """Document chunk model for storing document segments with embeddings."""

    __tablename__ = "chunks"

    chunk_id = Column(BigInteger, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    document_id = Column(
        BigInteger, ForeignKey("documents.document_id"), nullable=False
    )
    chunk_sequence_in_document = Column(BigInteger, nullable=False)

    # Vector embedding column using pgvector - 768 dimensions for legal-bert-base-uncased
    embedding = Column(pgvector.Vector(768), nullable=True)

    # Add index on the embedding column for similarity search
    __table_args__ = (
        Index(
            "chunk_embedding_index",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
    )
