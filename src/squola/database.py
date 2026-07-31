"""Database connection and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from squola.models import Base

# Default database path - SQLite for now, prepared for future DB migration
DATABASE_URL = "sqlite:///./db/squola.db"


def get_engine(database_url: str = DATABASE_URL):
    """Create database engine."""
    # SQLite specific: check_same_thread=False needed for FastAPI
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(database_url, connect_args=connect_args)


def create_session_factory(engine) -> sessionmaker[Session]:
    """Create session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Default engine and session factory
engine = get_engine()
SessionLocal = create_session_factory(engine)


def init_db() -> None:
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
