"""Кольцевой буфер логов observer для GET /logs."""

from __future__ import annotations

import logging
from collections import deque
from threading import Lock


class RingLogHandler(logging.Handler):
    def __init__(self, maxlen: int = 500) -> None:
        super().__init__()
        self._buf: deque[str] = deque(maxlen=maxlen)
        self._lock = Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        with self._lock:
            self._buf.append(msg)

    def lines(self, limit: int = 100) -> list[str]:
        with self._lock:
            items = list(self._buf)
        if limit <= 0:
            return items
        return items[-limit:]


_handler: RingLogHandler | None = None


def install_log_buffer(logger_name: str = "observer", maxlen: int = 500) -> RingLogHandler:
    global _handler
    if _handler is not None:
        return _handler
    _handler = RingLogHandler(maxlen=maxlen)
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger(logger_name).addHandler(_handler)
    # Также uvicorn/print через root иногда полезен — цепляем observer.*
    logging.getLogger("observer").setLevel(logging.INFO)
    return _handler


def get_log_lines(limit: int = 100) -> list[str]:
    if _handler is None:
        return []
    return _handler.lines(limit)
