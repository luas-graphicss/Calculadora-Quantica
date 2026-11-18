import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.conditions import UndefinedExpressionError, analyze_interval
from quantum_calculator.algebra.identity import IdentityTester
from quantum_calculator.domain.expressions import Expression, Integral
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport
from quantum_calculator.domain.verification import (
    EvidenceKind,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from quantum_calculator.notation.rendering.conditions import render_condition, render_conditions
from quantum_calculator.verification.evidence import (
    declared_domain_check,
    dimension_check,
    identity_check,
)
from quantum_calculator.verification.reporting import CALCULUS_REFERENCE, verification_report

_PRIMITIVE_CHECK = "primitive_derivative"
_PRIMITIVE_STATEMENT = (
    "A derivada da primitiva informada é o integrando, no domínio em que ele está definido."
)
_INTERVAL_CHECK = "interval_free_of_singularities"
_INTERVAL_STATEMENT = (
    "O integrando e a primitiva não têm singularidade no intervalo de integração fechado."
)
_VALUE_CHECK = "fundamental_theorem_value"
_VALUE_STATEMENT = (
    "O valor informado é a diferença da primitiva entre o limite superior e o inferior."
)


class AntiderivativeVerifier:
    def __init__(self, tester: IdentityTester | None = None) -> None:
        self._tester = tester or IdentityTester()

    def verify(
        self, problem: ValidatedStatement, report: SymbolicSolverReport
    ) -> VerificationReport:
        integral = _integral_of(problem)
        builder = ExpressionBuilder(problem.symbols, report.arbitrary_constants)
        return verification_report(
            [
                _primitive_check(self._tester, builder, integral, report.answer.right),
                declared_domain_check(problem, builder, integral.body),
                dimension_check(problem, report),
            ],
            CALCULUS_REFERENCE,
        )


class DefiniteIntegralVerifier:
    def __init__(self, tester: IdentityTester | None = None) -> None:
        self._tester = tester or IdentityTester()

    def verify(
        self, problem: ValidatedStatement, report: SymbolicSolverReport
    ) -> VerificationReport:
        integral = _integral_of(problem)
        builder = ExpressionBuilder(problem.symbols)
        primitive = report.certificate
        if primitive is None or integral.bounds is None:
            return verification_report([_missing_primitive()], CALCULUS_REFERENCE)
        variable = builder.symbol(integral.variable)
        antiderivative = builder.build(primitive)
        difference = antiderivative.subs(
            variable, builder.build(integral.bounds.upper)
        ) - antiderivative.subs(variable, builder.build(integral.bounds.lower))
        claimed = builder.build(report.answer.right)
        return verification_report(
            [
                _primitive_check(self._tester, builder, integral, primitive),
                _interval_check(builder, integral, primitive),
                identity_check(
                    _VALUE_CHECK, _VALUE_STATEMENT, self._tester.test(claimed - difference)
                ),
                dimension_check(problem, report),
            ],
            CALCULUS_REFERENCE,
        )


def _integral_of(problem: ValidatedStatement) -> Integral:
    if not isinstance(problem.statement, Integral):
        raise TypeError("the primitive check needs an integral statement")
    return problem.statement


def _primitive_check(
    tester: IdentityTester, builder: ExpressionBuilder, integral: Integral, primitive: Expression
) -> VerificationCheck:
    variable = builder.symbol(integral.variable)
    residual = sympy.diff(builder.build(primitive), variable) - builder.build(integral.body)
    return identity_check(_PRIMITIVE_CHECK, _PRIMITIVE_STATEMENT, tester.test(residual))


def _interval_check(
    builder: ExpressionBuilder, integral: Integral, primitive: Expression
) -> VerificationCheck:
    try:
        analysis = analyze_interval(builder, integral, integral.body, primitive)
    except UndefinedExpressionError as error:
        return _interval_outcome(
            VerificationStatus.FAILED,
            f"o integrando exige {render_condition(error.condition)}, que nunca vale",
        )
    if analysis.singularities:
        found = "; ".join(
            f"{render_condition(singularity.condition)} falha em {singularity.location}"
            for singularity in analysis.singularities
        )
        return _interval_outcome(VerificationStatus.FAILED, found)
    if analysis.assumptions:
        return _interval_outcome(
            VerificationStatus.CONDITIONAL,
            f"vale somente com {render_conditions(analysis.assumptions)}, o que os limites e "
            "parâmetros declarados não decidem",
        )
    return _interval_outcome(
        VerificationStatus.PASSED, "nenhuma condição de definição falha entre os limites"
    )


def _interval_outcome(status: VerificationStatus, observed: str) -> VerificationCheck:
    return VerificationCheck(
        _INTERVAL_CHECK, EvidenceKind.PROOF, status, _INTERVAL_STATEMENT, observed
    )


def _missing_primitive() -> VerificationCheck:
    return VerificationCheck(
        _PRIMITIVE_CHECK,
        EvidenceKind.PROOF,
        VerificationStatus.FAILED,
        _PRIMITIVE_STATEMENT,
        "o resultado veio sem a primitiva que permitiria conferi-lo",
    )
