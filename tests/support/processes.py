import time
from collections.abc import Callable, Iterator
from pathlib import Path

_PROCESS_TABLE = Path("/proc")
_PARENT = 1
_SESSION = 3
_POLL_SECONDS = 0.01


def has_child_running(parent: int, command_fragment: bytes) -> bool:
    return bool(children_running(parent, command_fragment))


def children_running(parent: int, command_fragment: bytes) -> list[int]:
    return [
        identifier
        for identifier, fields, command in _processes()
        if fields[_PARENT] == str(parent) and command_fragment in command
    ]


def session_is_empty(session: int) -> bool:
    return not any(fields[_SESSION] == str(session) for _, fields, _ in _processes())


def wait_until(condition: Callable[[], bool], seconds: float = 30.0) -> None:
    deadline = time.monotonic() + seconds
    while not condition():
        if time.monotonic() >= deadline:
            raise AssertionError(f"condition not met within {seconds:g} s")
        time.sleep(_POLL_SECONDS)


def _processes() -> Iterator[tuple[int, list[str], bytes]]:
    for entry in _PROCESS_TABLE.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            status = (entry / "stat").read_text("utf-8", "replace")
            command = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        yield int(entry.name), status.rsplit(")", 1)[1].split(), command
