import logging
from logging.handlers import RotatingFileHandler

from src.utils.path_resolve import find_project_root_by_src


LOG_FILE = "bot.log"


def setup_logging() -> logging.Logger:
    root_dir = find_project_root_by_src()
    logs_dir = root_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / LOG_FILE

    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Logger is working!")
