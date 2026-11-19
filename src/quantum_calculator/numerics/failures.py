from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, ProblemRejectedError

_NOTHING_APPROVED = "Nenhuma resposta foi aprovada."
_SOLVABLE = "um problema que o método homologado resolva dentro das tolerâncias pedidas"
_FINITE = "um problema cujos valores intermediários e finais sejam finitos"


def method_not_converged(method: str, reason: str) -> ProblemRejectedError:
    return ProblemRejectedError(
        (
            Diagnostic(
                DiagnosticCode.METHOD_NOT_CONVERGED,
                "",
                f"O método {method} não convergiu: {reason} {_NOTHING_APPROVED}",
                _SOLVABLE,
            ),
        )
    )


def non_finite_result(subject: str) -> ProblemRejectedError:
    return ProblemRejectedError(
        (
            Diagnostic(
                DiagnosticCode.NON_FINITE_RESULT,
                "",
                f"{subject} não é finito. {_NOTHING_APPROVED}",
                _FINITE,
            ),
        )
    )
