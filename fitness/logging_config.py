import logging
from logging.handlers import RotatingFileHandler
from .config import LOG_DIR


def configure_logging(level=logging.INFO):
    """Configure console and rotating file logs without duplicate handlers."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(level)
    if logger.handlers:
        return
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler = RotatingFileHandler(
        LOG_DIR / "fitness_app.log", maxBytes=1_000_000, backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
