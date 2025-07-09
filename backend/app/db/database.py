from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Database URL resolution with fallback to local Postgres instance
DATABASE_URL: str = (
    settings.database_url
    or "postgresql+psycopg2://postgres:password@localhost:5432/goquant"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=settings.log_sql_queries and not settings.is_production,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model for declarative class definitions
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Import models to ensure they are registered on the metadata
# (The app.db __init__ will import models, so it's safe to omit here.) 