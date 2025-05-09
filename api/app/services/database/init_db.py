"""PostgreSQL database initialization.

Enables pgvector extension and creates tables.
"""

import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.services.database.database import Base, engine
from pgvector.psycopg import register_vector

logger = logging.getLogger(__name__)


def init_vector_db():
    """Initialize PostgreSQL with pgvector and create tables.

    Creates the vector extension if not exists and initializes
    all tables defined in the models.
    """
    try:
        # Enable pgvector extension
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("Vector extension enabled in PostgreSQL")

            # Register the vector type with psycopg at initialization
            # No need to register here, we'll do it per connection when needed
            # as SQLAlchemy connection pooling makes this complex

        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        return True
    except SQLAlchemyError as e:
        logger.error(f"Error initializing vector database: {e}")
        raise
