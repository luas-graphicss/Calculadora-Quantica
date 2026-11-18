from dataclasses import dataclass
from enum import StrEnum


class ResultNature(StrEnum):
    EXACT = "exact"
    APPROXIMATE = "approximate"


@dataclass(frozen=True, slots=True)
class MethodDescription:
    identifier: str
    nature: ResultNature
    justification: str
    covariance_models: tuple[str, ...]
