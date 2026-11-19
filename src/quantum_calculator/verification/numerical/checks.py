from quantum_calculator.domain.verification import (
    EvidenceKind,
    VerificationCheck,
    VerificationStatus,
)


def scientific(value: float) -> str:
    return f"{value:.3e}"


def bounded_check(
    identifier: str,
    kind: EvidenceKind,
    statement: str,
    measured: float,
    limit: float,
    quantity: str,
) -> VerificationCheck:
    is_within = measured <= limit
    relation = "dentro do" if is_within else "acima do"
    return VerificationCheck(
        identifier,
        kind,
        VerificationStatus.PASSED if is_within else VerificationStatus.FAILED,
        statement,
        f"{quantity} {scientific(measured)}, {relation} limite {scientific(limit)}",
    )


def inconclusive_check(
    identifier: str, kind: EvidenceKind, statement: str, observed: str
) -> VerificationCheck:
    return VerificationCheck(identifier, kind, VerificationStatus.INCONCLUSIVE, statement, observed)
