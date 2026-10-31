"""
Database Connection and Session Management for LotTrace AI.
Provides SQLAlchemy engine, sessionmaker, and database lifecycle helpers.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config import DATABASE_URL, DATABASE_PATH, ensure_directories

Base = declarative_base()

# Configure SQLite PRAGMAs for referential integrity and performance
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass
    finally:
        cursor.close()


def get_engine(db_url: str = DATABASE_URL) -> Engine:
    """Creates and returns the SQLAlchemy engine."""
    ensure_directories()
    # Connect args for SQLite
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    return create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        future=True,
    )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(db_engine: Engine = engine) -> None:
    """Initializes all database tables registered with Base."""
    ensure_directories()
    # Import all models to ensure they are registered with Base metadata
    import src.models.entities  # noqa: F401
    Base.metadata.create_all(bind=db_engine)


def drop_db(db_engine: Engine = engine) -> None:
    """Drops all database tables registered with Base."""
    import src.models.entities  # noqa: F401
    Base.metadata.drop_all(bind=db_engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database transactional sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """Dependency for Flask route injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
