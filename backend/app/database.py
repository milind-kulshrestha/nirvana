"""Database configuration and session management."""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Ensure ~/.nirvana directory exists for SQLite
if settings.is_sqlite:
    db_dir = os.path.join(os.path.expanduser("~"), ".nirvana")
    os.makedirs(db_dir, exist_ok=True)

# Create database engine with appropriate args
engine_kwargs = {"echo": settings.DEBUG}
if settings.is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Enable WAL mode and foreign keys for SQLite
if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def init_db():
    """Create all tables (used in SQLite / single-user mode instead of Alembic)."""
    from app.models import (
        User, Watchlist, WatchlistItem, Conversation,
        Message, MemoryFact, PendingAction, Skill, EtfCustomSymbol,
    )
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
