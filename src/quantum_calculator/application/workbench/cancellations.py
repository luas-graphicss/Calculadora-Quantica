import threading

from quantum_calculator.domain.execution import CancellationSignal


class RunCancellations:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._signals: dict[str, threading.Event] = {}

    def open(self, identifier: str) -> CancellationSignal:
        with self._lock:
            return self._signals.setdefault(identifier, threading.Event())

    def request(self, identifier: str) -> None:
        with self._lock:
            signal = self._signals.get(identifier)
        if signal is not None:
            signal.set()

    def request_all(self) -> None:
        with self._lock:
            signals = tuple(self._signals.values())
        for signal in signals:
            signal.set()

    def close(self, identifier: str) -> None:
        with self._lock:
            self._signals.pop(identifier, None)
