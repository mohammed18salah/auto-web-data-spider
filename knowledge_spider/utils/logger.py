"""
Module: utils/logger.py
Purpose: Centralized loguru logger setup with rotating file output and
         rich-formatted console output. All modules import from here.
Author: KnowledgeSpider Engine
"""

import sys
from pathlib import Path
from loguru import logger as _logger


# ── Constants ────────────────────────────────────────────────────────────────
LOG_DIR: Path = Path("./logs")
LOG_FILE: Path = LOG_DIR / "knowledge_spider.log"
LOG_ROTATION: str = "10 MB"
LOG_RETENTION: str = "7 days"
LOG_LEVEL_FILE: str = "DEBUG"
LOG_LEVEL_CONSOLE: str = "INFO"

CONSOLE_FORMAT: str = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

FILE_FORMAT: str = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} - {message}"
)


def setup_logger(session_id: str = "global") -> None:
    """
    Configure loguru with console + rotating file sinks.

    Args:
        session_id: Optional session identifier appended to log filename.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Remove all default handlers
    _logger.remove()

    # ── Console sink (INFO and above, colourised) ─────────────────────────
    _logger.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level=LOG_LEVEL_CONSOLE,
        colorize=True,
        enqueue=True,
    )

    # ── Rotating file sink (DEBUG and above, plain text) ──────────────────
    session_log: Path = LOG_DIR / f"spider_{session_id}.log"
    _logger.add(
        str(session_log),
        format=FILE_FORMAT,
        level=LOG_LEVEL_FILE,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        enqueue=True,
        encoding="utf-8",
    )

    _logger.debug(f"Logger initialised. Session log → {session_log}")


def get_logger() -> "logger":  # type: ignore[name-defined]
    """
    Return the global loguru logger instance.

    Returns:
        The configured loguru logger.
    """
    return _logger


# ── Module-level convenience export ──────────────────────────────────────────
# Other modules do:  from knowledge_spider.utils.logger import logger
logger = _logger
