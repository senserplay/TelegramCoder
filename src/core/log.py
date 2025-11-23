import logging
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List

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


def get_log_file_path() -> Path:
    root_dir = find_project_root_by_src()
    return root_dir / "logs" / LOG_FILE


def read_last_n_lines(filepath: Path, n: int = 100) -> List[str]:
    if not filepath.exists():
        return [f"⚠️ Лог-файл не найден: {filepath}"]

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return list(deque(f, maxlen=n))
    except Exception as e:
        return [f"❌ Ошибка чтения лога: {e}"]


def read_full_log(filepath: Path) -> str:
    if not filepath.exists():
        return f"⚠️ Лог-файл не найден: {filepath}"
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"❌ Ошибка чтения лога: {e}"


if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Logger is working!")
