"""Database connection pooling and engine management using SQLAlchemy."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import QueuePool, StaticPool

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

_ENGINE: Engine | None = None


def get_db_engine(settings: Settings | None = None, force_new: bool = False) -> Engine:
    """Initialize or retrieve the singleton SQLAlchemy Engine with connection pooling."""
    global _ENGINE
    if _ENGINE is not None and not force_new:
        return _ENGINE

    cfg = settings or get_settings()
    db_url = cfg.get_database_url()

    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    else:
        # MySQL connection with connection pooling
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )

    if not force_new:
        _ENGINE = engine
    return engine


@contextmanager
def get_db_connection(engine: Engine | None = None) -> Generator:
    """Context manager for acquiring a database connection with auto-commit and rollback."""
    eng = engine or get_db_engine()
    connection = eng.connect()
    transaction = connection.begin()
    try:
        yield connection
        transaction.commit()
    except Exception as exc:
        transaction.rollback()
        logger.error(f"Database transaction rolled back due to error: {exc}")
        raise
    finally:
        connection.close()


def reconnect_db_engine(
    settings: Settings | None = None, max_retries: int = 3, retry_delay: float = 0.5
) -> Engine:
    """Force re-initialize the database engine with retry logic if the existing connection is unhealthy."""
    global _ENGINE
    import time
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting database reconnection (attempt {attempt}/{max_retries})...")
            new_engine = get_db_engine(settings=settings, force_new=True)
            with new_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _ENGINE = new_engine
            logger.info("Database reconnection successful.")
            return new_engine
        except Exception as exc:
            logger.warning(f"Database reconnection attempt {attempt} failed: {exc}")
            if attempt < max_retries:
                time.sleep(retry_delay)
    raise OperationalError("Failed to reconnect to database after maximum retries.", params=None, orig=Exception())


def check_db_connection(engine: Engine | None = None, auto_reconnect: bool = True) -> bool:
    """Verify database health by executing a lightweight SELECT 1 query with auto-reconnect fallback."""
    try:
        eng = engine or get_db_engine()
        with eng.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return result == 1
    except (OperationalError, SQLAlchemyError) as err:
        logger.warning(f"Database health check failed: {err}")
        if auto_reconnect and engine is None:
            try:
                reconnect_db_engine(max_retries=2, retry_delay=0.2)
                return True
            except Exception:
                return False
        return False
