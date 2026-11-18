import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.reader import UnregisteredOperationError, read_expression
from quantum_calculator.domain.expressions import Derivative, Equation, Expression
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport, SymbolicStep
from quantum_calculator.solvers.symbolic.results import read_result, solution_domain


class DifferentiationSolver:
    def solve(self, problem: ValidatedStatement) -> SymbolicSolverReport:
        derivative = problem.statement
        if not isinstance(derivative, Derivative):
            raise TypeError("differentiation needs a derivative statement")
        builder = ExpressionBuilder(problem.symbols)
        solution_domain(problem, builder, derivative.body)
        variable = builder.symbol(derivative.variable)
        unsimplified = sympy.diff(builder.build(derivative.body), variable, derivative.order)
        value = read_result(sympy.simplify(unsimplified))
        domain = solution_domain(problem, builder, derivative.body, value)
        return SymbolicSolverReport(
            answer=Equation(derivative, value),
            nature=ResultNature.EXACT,
            validity=domain.validity,
            assumptions=domain.assumptions,
            special_cases=(),
            arbitrary_constants=(),
            certificate=None,
            steps=_steps(unsimplified, value),
        )


def _steps(unsimplified: sympy.Expr, value: Expression) -> tuple[SymbolicStep, ...]:
    simplified = SymbolicStep("Resultado simplificado", value)
    try:
        before = read_expression(unsimplified)
    except UnregisteredOperationError:
        return (simplified,)
    if before == value:
        return (SymbolicStep("Derivada pelas regras de derivação", value),)
    return (
        SymbolicStep("Derivada pelas regras de derivação, antes de simplificar", before),
        simplified,
    )
