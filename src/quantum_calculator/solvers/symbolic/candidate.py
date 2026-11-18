from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.domain.expressions import Equation
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport
from quantum_calculator.solvers.symbolic.linear_form import linear_form
from quantum_calculator.solvers.symbolic.results import solution_domain


class CandidateClaim:
    def solve(self, problem: ValidatedStatement) -> SymbolicSolverReport:
        equation = problem.statement
        candidate = problem.candidate
        if candidate is None or not isinstance(equation, Equation):
            raise TypeError("a review needs a differential equation and a candidate solution")
        function = problem.unknown
        builder = ExpressionBuilder(problem.symbols)
        linear_form(
            builder.build(equation.left) - builder.build(equation.right),
            builder.unknown(function.name),
            builder.symbol(function.require_argument()),
        )
        domain = solution_domain(problem, builder, equation, *problem.conditions, candidate)
        return SymbolicSolverReport(
            answer=candidate,
            nature=ResultNature.EXACT,
            validity=domain.validity,
            assumptions=domain.assumptions,
            special_cases=(),
            arbitrary_constants=(),
            certificate=None,
            steps=(),
        )
