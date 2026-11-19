from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BackupReport:
    runs: int
    artifacts: int
    size: int


@dataclass(frozen=True, slots=True)
class RestoreReport:
    runs: int
    artifacts: int
    written_by: str
    storage_schema: int
    current_storage_schema: int


class BackupRejectedError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
