from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PackageFile:
    path: str
    content: bytes


class PackageRejectedError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
