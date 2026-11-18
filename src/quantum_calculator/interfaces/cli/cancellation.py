import signal
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from types import FrameType

from quantum_calculator.domain.execution import CancellationSignal


@contextmanager
def interrupt_cancellation() -> Iterator[CancellationSignal]:
    requested = threading.Event()

    def request(_signal_number: int, _frame: FrameType | None) -> None:
        requested.set()

    previous = signal.signal(signal.SIGINT, request)
    try:
        yield requested
    finally:
        signal.signal(signal.SIGINT, previous)
