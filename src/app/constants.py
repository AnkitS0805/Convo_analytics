from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConstants:
    db_url: str = os.getenv('DB_URL', 'sqlite:///data/adventureworks.db')
    archive_dir: str = os.getenv('ARCHIVE_DIR', 'data/archive')
    max_preview_rows: int = int(os.getenv('MAX_PREVIEW_ROWS', '100'))
    sql_timeout_seconds: int = int(os.getenv('SQL_TIMEOUT_SECONDS', '30'))
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    aws_region: str = os.getenv('AWS_REGION', 'us-east-1')
    bedrock_model_id: str = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')
ALLOWED_TABLES = {'SalesOrderHeader', 'SalesOrderDetail', 'Product', 'ProductSubcategory', 'ProductCategory', 'Customer', 'Person', 'SalesTerritory'}
