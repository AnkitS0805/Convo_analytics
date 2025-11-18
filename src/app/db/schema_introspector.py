"""Schema introspection utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from sqlalchemy import inspect
from sqlalchemy.engine import Engine


@dataclass
class TableSchema:
    name: str
    columns: List[Dict]


def introspect_schema(engine: Engine) -> List[TableSchema]:
    inspector = inspect(engine)
    tables = []
    for t in inspector.get_table_names():
        cols = [
            {
                "name": c["name"],
                "type": str(c["type"]),
                "nullable": c["nullable"],
                "default": str(c.get("default")),
            }
            for c in inspector.get_columns(t)
        ]
        tables.append(TableSchema(name=t, columns=cols))
    return tables
