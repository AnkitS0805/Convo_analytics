"""Database engine and session helpers using SQLAlchemy."""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..constants import AppConstants
from ..logging_config import get_logger

logger = get_logger(__name__)


def get_engine() -> Engine:
    """Create or reuse a SQLAlchemy engine for the configured DB URL."""
    url = AppConstants().db_url
    logger.info("Connecting to DB: %s", url)
    engine = create_engine(url, future=True)
    # Simple connectivity check
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine
