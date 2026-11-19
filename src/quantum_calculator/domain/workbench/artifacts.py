from dataclasses import dataclass

JSON_MEDIA_TYPE = "application/json"


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    sha256: str
    media_type: str
    size: int


class ArtifactIntegrityError(Exception):
    def __init__(self, sha256: str, reason: str) -> None:
        super().__init__(f"artifact {sha256} failed its integrity check: {reason}")
        self.sha256 = sha256
        self.reason = reason
