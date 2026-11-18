from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.identity import IdentityTester
from quantum_calculator.algebra.reader import UnregisteredOperationError
from quantum_calculator.domain.expressions import Derivative
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport
from quantum_calculator.domain.verification import (
    EvidenceKind,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from quantum_calculator.verification.differentiation_rules import derive_by_rules
from quantum_calculator.verification.evidence import (
    declared_domain_check,
    dimension_check,
    identity_check,
)
from quantum_calculator.verification.reporting import CALCULUS_REFERENCE, verification_report

_RULES_CHECK = "rule_by_rule_derivative"
_RULES_STATEMENT = (
    "A derivada informada coincide com a obtida aplicando à expressão original as regras "
    "da soma, do produto, do quociente, da potência e da cadeia."
)


class DifferentiationVerifier:
    def __init__(self, tester: IdentityTester | None = None) -> None:
        self._tester = tester or IdentityTester()

    def verify(
        self, problem: ValidatedStatement, report: SymbolicSolverReport
    ) -> VerificationReport:
        derivative = problem.statement
        if not isinstance(derivative, Derivative):
            raise TypeError("the differentiation rules check a derivative statement")
        builder = ExpressionBuilder(problem.symbols)
        claimed = report.answer.right
        return verification_report(
            [
                self._rules_check(derivative, builder, report),
                declared_domain_check(problem, builder, derivative.body, claimed),
                dimension_check(problem, report),
            ],
            CALCULUS_REFERENCE,
        )

    def _rules_check(
        self, derivative: Derivative, builder: ExpressionBuilder, report: SymbolicSolverReport
    ) -> VerificationCheck:
        try:
            expected = derive_by_rules(derivative, builder)
        except UnregisteredOperationError as error:
            return VerificationCheck(
                _RULES_CHECK,
                EvidenceKind.PROOF,
                VerificationStatus.INCONCLUSIVE,
                _RULES_STATEMENT,
                f"a derivação regra a regra saiu das operações registradas em {error.operation}",
            )
        residual = builder.build(report.answer.right) - expected
        return identity_check(_RULES_CHECK, _RULES_STATEMENT, self._tester.test(residual))
