import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.identity import IdentityTester
from quantum_calculator.domain.expressions import Equation, UnknownFunction
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport
from quantum_calculator.domain.verification import (
    SkippedCheck,
    VerificationCheck,
    VerificationReport,
)
from quantum_calculator.verification.evidence import (
    declared_domain_check,
    dimension_check,
    identity_check,
)
from quantum_calculator.verification.reporting import (
    LINEAR_EQUATION_REFERENCE,
    verification_report,
)

_EQUATION_CHECK = "equation_residual"
_EQUATION_STATEMENT = (
    "A função informada, substituída na equação original, anula a diferença entre os dois lados."
)
_CONDITION_CHECK = "initial_condition"
_CONDITION_STATEMENT = "A função informada assume o valor declarado no ponto da condição inicial."
_NO_CONDITION = (
    "Nenhuma condição inicial foi declarada: a resposta é uma família com constante arbitrária."
)


class OdeSubstitutionVerifier:
    def __init__(self, tester: IdentityTester | None = None) -> None:
        self._tester = tester or IdentityTester()

    def verify(
        self, problem: ValidatedStatement, report: SymbolicSolverReport
    ) -> VerificationReport:
        equation = problem.statement
        if not isinstance(equation, Equation):
            raise TypeError("substitution needs a differential equation")
        function = problem.unknown
        builder = ExpressionBuilder(problem.symbols, report.arbitrary_constants)
        solution = builder.build(report.answer.right)
        sides = builder.build(equation.left) - builder.build(equation.right)
        residual = sides.subs(builder.unknown(function.name), solution).doit()
        return verification_report(
            [
                identity_check(_EQUATION_CHECK, _EQUATION_STATEMENT, self._tester.test(residual)),
                self._condition_outcome(problem, builder, solution),
                declared_domain_check(
                    problem, builder, equation, *problem.conditions, report.answer
                ),
                dimension_check(problem, report),
            ],
            LINEAR_EQUATION_REFERENCE,
        )

    def _condition_outcome(
        self, problem: ValidatedStatement, builder: ExpressionBuilder, solution: sympy.Expr
    ) -> VerificationCheck | SkippedCheck:
        if not problem.conditions:
            return SkippedCheck(_CONDITION_CHECK, _NO_CONDITION)
        condition = problem.conditions[0]
        if not isinstance(condition.left, UnknownFunction):
            raise TypeError("an initial condition fixes the unknown function at a point")
        variable = builder.symbol(problem.unknown.require_argument())
        at_point = solution.subs(variable, builder.build(condition.left.argument))
        residual = at_point - builder.build(condition.right)
        return identity_check(_CONDITION_CHECK, _CONDITION_STATEMENT, self._tester.test(residual))
