"""Database ORM models.

This module contains SQLAlchemy ORM models for database operations.
Using pgvector for vector storage and retrieval.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import pgvector.sqlalchemy as pgvector
from typing import List, Optional

from app.services.database.database import Base


class Document(Base):
    """Document ORM model for storing documents in the database."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=False)
    metadata = Column(JSON, nullable=True)
    file_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # One-to-many relationship with document chunks
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """Document chunk model for storing document segments with embeddings."""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)

    # Vector embedding column using pgvector - 768 dimensions for legal-bert-base-uncased
    embedding = Column(pgvector.Vector(768), nullable=True)

    # Add index on the embedding column for similarity search (this will be used for vector similarity search)
    __table_args__ = (
        pgvector.IvfflatIndex(
            "embedding",
            lists=100,  # Number of lists to create, can be tuned based on data size
        ),
    )

    # Many-to-one relationship with document
    document = relationship("Document", back_populates="chunks")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
