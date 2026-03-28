"""
logging_config.py
-----------------
Configures structured logging for the trading bot.
Logs are written to both a rotating file (logs/bot.log) and the console (WARNING+).
"""

import logging
import logging.handlers
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "bot.log"

# ── Log format ─────────────────────────────────────────────────────────────────
FILE_FMT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)
CONSOLE_FMT = "%(levelname)-8s | %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "DEBUG") -> None:
    """
    Call once at application startup to initialise logging.

    Args:
        log_level: Minimum level written to the log FILE (default DEBUG).
                   The console handler always starts at WARNING.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)           # let handlers filter individually

    # ── Remove any handlers added by imported libraries ────────────────────
    root.handlers.clear()

    # ── Rotating file handler (10 MB × 5 backups) ─────────────────────────
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(numeric_level)
    fh.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))

    # ── Console handler (WARNING and above so output stays clean) ─────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter(CONSOLE_FMT))

    root.addHandler(fh)
    root.addHandler(ch)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("binance").setLevel(logging.WARNING)

    logging.getLogger(__name__).debug(
        "Logging initialised. File → %s  |  Level → %s", LOG_FILE, log_level
    )
