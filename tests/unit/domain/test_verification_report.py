import pytest

from quantum_calculator.domain.verification import (
    EvidenceKind,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)

PASSED = VerificationStatus.PASSED
CONDITIONAL = VerificationStatus.CONDITIONAL
INCONCLUSIVE = VerificationStatus.INCONCLUSIVE
FAILED = VerificationStatus.FAILED


def _report(statuses: tuple[VerificationStatus, ...]) -> VerificationReport:
    checks = tuple(
        VerificationCheck(f"check_{index}", EvidenceKind.PROOF, status, "statement", "observed")
        for index, status in enumerate(statuses)
    )
    return VerificationReport(checks=checks, not_performed=(), references=())


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((PASSED, PASSED), PASSED),
        ((PASSED, CONDITIONAL), CONDITIONAL),
        ((CONDITIONAL, INCONCLUSIVE), INCONCLUSIVE),
        ((PASSED, INCONCLUSIVE, FAILED), FAILED),
    ],
)
def test_report_status_is_the_least_favourable_check(
    statuses: tuple[VerificationStatus, ...], expected: VerificationStatus
) -> None:
    assert _report(statuses).status is expected


def test_report_without_checks_is_inconclusive() -> None:
    assert _report(()).status is INCONCLUSIVE
