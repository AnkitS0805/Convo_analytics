
from __future__ import annotations

import pathlib
from typing import Dict

import pandas as pd
from sqlalchemy import create_engine

from ..constants import AppConstants
from ..logging_config import get_logger

logger = get_logger(__name__)


def _safe_table_name(name: str) -> str:
    return (
        name.replace(".csv", "")
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".", "_")
    )


def _read_csv_with_fallbacks(csv_path: pathlib.Path) -> pd.DataFrame:
   
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            logger.info("Reading %s with encoding=%s", csv_path.name, enc)
            return pd.read_csv(
                csv_path,
                encoding=enc,
                engine="python",
                sep=None,  # infer delimiter
                on_bad_lines="skip",
            )
        except UnicodeDecodeError as e:
            last_err = e
            continue
        except Exception as e:  # noqa: BLE001
            # Save and continue trying; we'll raise the last error if all fail
            last_err = e
            continue
    # If all attempts failed, raise the last error
    assert last_err is not None
    raise last_err


def main() -> None:
    cfg = AppConstants()
    archive = pathlib.Path(cfg.archive_dir)
    db_url = cfg.db_url

    archive.mkdir(parents=True, exist_ok=True)
    pathlib.Path("data").mkdir(parents=True, exist_ok=True)

    logger.info("Loading CSVs from: %s", archive)
    engine = create_engine(db_url, future=True)

    csv_files = sorted(archive.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in %s", archive)
        return

    for csv in csv_files:
        table = _safe_table_name(csv.name)
        logger.info("Loading %s -> table %s", csv.name, table)
        df = _read_csv_with_fallbacks(csv)
        # Normalize column names
        df.columns = [c.strip().replace(" ", "_") for c in df.columns]
        df.to_sql(table, engine, if_exists="replace", index=False)

    logger.info("ETL completed. Database created at %s", db_url)


if __name__ == "__main__":
    main()
