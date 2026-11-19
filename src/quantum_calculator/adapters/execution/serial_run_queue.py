import logging
import queue
import threading
from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)


class SerialRunQueue:
    def __init__(self, execute: Callable[[str], None]) -> None:
        self._execute = execute
        self._pending: queue.SimpleQueue[str | None] = queue.SimpleQueue()
        self._worker = threading.Thread(target=self._drain, name="qcalc-run-worker", daemon=True)
        self._worker.start()

    def enqueue(self, identifier: str) -> None:
        self._pending.put(identifier)

    def close(self) -> None:
        self._pending.put(None)
        self._worker.join()

    def _drain(self) -> None:
        while (identifier := self._pending.get()) is not None:
            try:
                self._execute(identifier)
            except Exception:
                _LOGGER.exception("run %s ended with an unexpected error", identifier)
