from dataclasses import dataclass
from enum import StrEnum


class VerificationStatus(StrEnum):
    PASSED = "passed"
    CONDITIONAL = "conditional"
    INCONCLUSIVE = "inconclusive"
    FAILED = "failed"


class EvidenceKind(StrEnum):
    PROOF = "proof"
    CONSISTENCY_TEST = "consistency_test"


_LEAST_FAVOURABLE_FIRST = (
    VerificationStatus.FAILED,
    VerificationStatus.INCONCLUSIVE,
    VerificationStatus.CONDITIONAL,
)


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    identifier: str
    kind: EvidenceKind
    status: VerificationStatus
    statement: str
    observed: str


@dataclass(frozen=True, slots=True)
class SkippedCheck:
    identifier: str
    reason: str


@dataclass(frozen=True, slots=True)
class VerificationReport:
    checks: tuple[VerificationCheck, ...]
    not_performed: tuple[SkippedCheck, ...]
    references: tuple[str, ...]

    @property
    def status(self) -> VerificationStatus:
        if not self.checks:
            return VerificationStatus.INCONCLUSIVE
        observed = {check.status for check in self.checks}
        for status in _LEAST_FAVOURABLE_FIRST:
            if status in observed:
                return status
        return VerificationStatus.PASSED
