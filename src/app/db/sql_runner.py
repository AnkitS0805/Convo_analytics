"""Safe SQL execution utilities."""
from __future__ import annotations

import contextlib
import sqlite3
from dataclasses import dataclass
from typing import Any, List, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..constants import ALLOWED_TABLES, AppConstants
from ..logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SqlResult:
    columns: List[str]
    rows: List[Tuple[Any, ...]]
    row_count: int


def validate_sql(sql: str) -> None:
    """Very lightweight guard: ensure query references only allowlisted tables."""
    lowered = sql.lower()
    for t in ALLOWED_TABLES:
        if t.lower() in lowered:
            break
    else:
        logger.warning("SQL does not reference any allowlisted table.")


def run_sql(engine: Engine, sql: str, preview: bool = True) -> SqlResult:
    validate_sql(sql)
    max_rows = AppConstants().max_preview_rows if preview else None
    timeout = AppConstants().sql_timeout_seconds

    # Apply LIMIT for SQLite if preview
    if preview and "limit" not in sql.lower():
        sql = f"{sql.strip()} LIMIT {max_rows}"

    logger.info("Executing SQL (preview=%s): %s", preview, sql)

    # Use pandas for convenience to fetch rows and columns
    with contextlib.closing(engine.connect()) as conn:
        if isinstance(conn.connection, sqlite3.Connection):
            conn.connection.set_trace_callback(None)
        df = pd.read_sql(text(sql), conn)

    rows = [tuple(x) for x in df.itertuples(index=False, name=None)]
    return SqlResult(columns=list(df.columns), rows=rows, row_count=len(rows))
