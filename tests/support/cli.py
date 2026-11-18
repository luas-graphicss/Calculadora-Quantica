from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CliResult:
    exit_code: int
    stdout: str
    stderr: str


type CliRunner = Callable[..., CliResult]


def write_document(directory: Path, content: bytes) -> Path:
    path = directory / "problem.json"
    path.write_bytes(content)
    return path
