import re
from collections.abc import Iterator
from pathlib import Path

_PROCESS_TABLE = Path("/proc")
_WORKER_COMMAND = b"spawn_main"
_HIGH_WATER_MARK = re.compile(rb"^VmHWM:\s+(\d+) kB$", re.MULTILINE)
_KIBIBYTE = 1024


class WorkerMemoryUnavailableError(Exception):
    def __init__(self, parent: int) -> None:
        super().__init__(
            f"/proc/{parent}/task/{parent}/children is missing: this kernel does not list the "
            "children of a process, so the worker cannot be found"
        )


def require_children_listing(parent: int) -> None:
    if not (_PROCESS_TABLE / str(parent) / "task" / str(parent) / "children").exists():
        raise WorkerMemoryUnavailableError(parent)


def worker_peak_rss_bytes(parent: int) -> int:
    return max((_worker_peak_rss_bytes(child) for child in _children(parent)), default=0)


def own_peak_rss_bytes() -> int:
    return _high_water_mark_bytes(_PROCESS_TABLE / "self")


def _children(parent: int) -> Iterator[int]:
    for listing in (_PROCESS_TABLE / str(parent) / "task").glob("*/children"):
        try:
            identifiers = listing.read_text("ascii").split()
        except OSError:
            continue
        yield from (int(identifier) for identifier in identifiers)


def _worker_peak_rss_bytes(process: int) -> int:
    entry = _PROCESS_TABLE / str(process)
    try:
        if _WORKER_COMMAND not in (entry / "cmdline").read_bytes():
            return 0
        return _high_water_mark_bytes(entry)
    except OSError:
        return 0


def _high_water_mark_bytes(entry: Path) -> int:
    match = _HIGH_WATER_MARK.search((entry / "status").read_bytes())
    return 0 if match is None else int(match.group(1)) * _KIBIBYTE
