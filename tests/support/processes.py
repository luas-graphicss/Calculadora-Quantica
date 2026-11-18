import time
from collections.abc import Callable, Iterator
from pathlib import Path

_PROCESS_TABLE = Path("/proc")
_PARENT = 1
_SESSION = 3
_POLL_SECONDS = 0.01


def has_child_running(parent: int, command_fragment: bytes) -> bool:
    return any(
        fields[_PARENT] == str(parent) and command_fragment in command
        for fields, command in _processes()
    )


def session_is_empty(session: int) -> bool:
    return not any(fields[_SESSION] == str(session) for fields, _ in _processes())


def wait_until(condition: Callable[[], bool], seconds: float = 30.0) -> None:
    deadline = time.monotonic() + seconds
    while not condition():
        if time.monotonic() >= deadline:
            raise AssertionError(f"condition not met within {seconds:g} s")
        time.sleep(_POLL_SECONDS)


def _processes() -> Iterator[tuple[list[str], bytes]]:
    for entry in _PROCESS_TABLE.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            status = (entry / "stat").read_text("utf-8", "replace")
            command = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        yield status.rsplit(")", 1)[1].split(), command
