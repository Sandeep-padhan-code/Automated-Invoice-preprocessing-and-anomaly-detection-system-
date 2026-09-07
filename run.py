from __future__ import annotations

import sys
import uvicorn
import config
from src.logging_config import setup_logger

logger = setup_logger("ledgerlens.runner")


def main() -> None:
    logger.info("Starting LedgerLens API Server in %s mode", config.ENVIRONMENT.upper())
    logger.info("Listening on http://%s:%d", config.HOST, config.PORT)
    logger.info("Allowed CORS origins: %s", config.ALLOWED_ORIGINS)
    logger.info("Max upload size: %d MB", config.MAX_UPLOAD_BYTES // (1024 * 1024))
    if config.API_KEY:
        logger.info("API Key protection: ENABLED")
    else:
        logger.info("API Key protection: DISABLED (development mode)")

    uvicorn.run(
        "backend:app",
        host=config.HOST,
        port=config.PORT,
        workers=config.WORKERS if config.IS_PRODUCTION else 1,
        reload=not config.IS_PRODUCTION,
        log_level=config.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
