from quantum_calculator.domain.verification import (
    SkippedCheck,
    VerificationCheck,
    VerificationReport,
)

CALCULUS_REFERENCE = "T. M. Apostol, Calculus, vol. 1, 2ª ed., Wiley, 1967, capítulos 4 e 5."
LINEAR_EQUATION_REFERENCE = (
    "W. E. Boyce e R. C. DiPrima, Elementary Differential Equations and Boundary Value "
    "Problems, 10ª ed., Wiley, 2012, seção 2.1."
)


def verification_report(
    outcomes: list[VerificationCheck | SkippedCheck], reference: str
) -> VerificationReport:
    return VerificationReport(
        checks=tuple(item for item in outcomes if isinstance(item, VerificationCheck)),
        not_performed=tuple(item for item in outcomes if isinstance(item, SkippedCheck)),
        references=(reference,),
    )
