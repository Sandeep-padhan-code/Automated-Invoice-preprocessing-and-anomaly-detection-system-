from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logger(name: str = "ledgerlens", level: Optional[str] = None) -> logging.Logger:
    """Configures and returns a structured logger."""
    import config

    log_level_str = level or getattr(config, "LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)
        logger.propagate = False

    return logger
