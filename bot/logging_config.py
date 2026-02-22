"""Настройка логирования в файл, консоль и удалённую БД."""
import asyncio
import logging
import queue
import sys
from pathlib import Path

_log_queue: queue.Queue = queue.Queue(maxsize=5000)
_SENTINEL = object()

class DatabaseLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname
            name = record.name or ""
            self._put(level, name, msg)
        except Exception:
            self.handleError(record)
    def _put(self, level: str, logger_name: str, message: str) -> None:
        try:
            _log_queue.put_nowait((level, logger_name, message))
        except queue.Full:
            pass

def setup_logging(log_dir: str | Path | None = None, log_level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(formatter)
    root.addHandler(console)
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "bot.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(log_level)
    db_handler.setFormatter(formatter)
    root.addHandler(db_handler)
    logging.getLogger("bot").info("Логирование инициализировано: %s", log_file)

async def consume_log_queue() -> None:
    from bot.database import insert_log
    while True:
        try:
            item = _log_queue.get(timeout=0.5)
        except queue.Empty:
            await asyncio.sleep(0)
            continue
        if item is _SENTINEL:
            break
        level, logger_name, message = item
        try:
            await insert_log(level, logger_name, message)
        except Exception:
            pass
        await asyncio.sleep(0)

def stop_log_queue() -> None:
    try:
        _log_queue.put_nowait(_SENTINEL)
    except queue.Full:
        _log_queue.put(_SENTINEL)
