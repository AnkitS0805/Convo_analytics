from __future__ import annotations
import logging
from logging import Logger
from .constants import AppConstants

def get_logger(name: str) -> Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = getattr(logging, AppConstants().log_level.upper(), logging.INFO)
        logger.setLevel(level)
        handler = logging.StreamHandler()
        fmt = logging.Formatter(fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger
