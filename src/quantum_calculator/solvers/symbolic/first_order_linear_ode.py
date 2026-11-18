from dataclasses import dataclass
from fractions import Fraction

import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.domain.expressions import (
    Equation,
    Expression,
    Number,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.statements import BoundSymbol, ValidatedStatement
from quantum_calculator.domain.symbolic_solution import (
    SpecialCase,
    SymbolicSolverReport,
    SymbolicStep,
)
from quantum_calculator.solvers.symbolic.linear_form import LinearForm, linear_form
from quantum_calculator.solvers.symbolic.results import (
    fresh_constant,
    read_result,
    solution_domain,
)

_ZERO = Number(Fraction(0))


@dataclass(frozen=True, slots=True)
class _InitialValue:
    point: sympy.Expr
    value: sympy.Expr


class FirstOrderLinearSolver:
    def solve(self, problem: ValidatedStatement) -> SymbolicSolverReport:
        equation = problem.statement
        if not isinstance(equation, Equation):
            raise TypeError("the closed form needs a differential equation")
        function = problem.unknown
        constants = () if problem.conditions else (fresh_constant(problem),)
        builder = ExpressionBuilder(problem.symbols, constants)
        variable = builder.symbol(function.require_argument())
        unknown = builder.unknown(function.name)
        residual = builder.build(equation.left) - builder.build(equation.right)
        form = linear_form(residual, unknown, variable)
        start = _initial_value(problem, builder)
        free = builder.symbol(constants[0]) if constants else None
        if form.rate.is_zero:
            solution = _drift(form, variable, start, free)
        else:
            solution = _relaxation(form, variable, start, free)
        answer = _solved_for(function, read_result(solution))
        domain = solution_domain(problem, builder, equation, *problem.conditions, answer)
        return SymbolicSolverReport(
            answer=answer,
            nature=ResultNature.EXACT,
            validity=domain.validity,
            assumptions=domain.assumptions,
            special_cases=_special_cases(form, function, variable, start, free),
            arbitrary_constants=constants,
            certificate=None,
            steps=(
                SymbolicStep("Forma normal da equação", _normal_form(function, form, unknown)),
                SymbolicStep("Solução em forma fechada", answer),
            ),
        )


def _initial_value(problem: ValidatedStatement, builder: ExpressionBuilder) -> _InitialValue | None:
    if not problem.conditions:
        return None
    condition = problem.conditions[0]
    if not isinstance(condition.left, UnknownFunction):
        raise TypeError("an initial condition fixes the unknown function at a point")
    return _InitialValue(builder.build(condition.left.argument), builder.build(condition.right))


def _relaxation(
    form: LinearForm,
    variable: sympy.Symbol,
    start: _InitialValue | None,
    free: sympy.Symbol | None,
) -> sympy.Expr:
    equilibrium = -form.source / form.rate
    if start is None:
        return equilibrium + free * sympy.exp(form.rate * variable)
    return equilibrium + (start.value - equilibrium) * sympy.exp(
        form.rate * (variable - start.point)
    )


def _drift(
    form: LinearForm,
    variable: sympy.Symbol,
    start: _InitialValue | None,
    free: sympy.Symbol | None,
) -> sympy.Expr:
    if start is None:
        return form.source * variable + free
    return start.value + form.source * (variable - start.point)


def _special_cases(
    form: LinearForm,
    function: BoundSymbol,
    variable: sympy.Symbol,
    start: _InitialValue | None,
    free: sympy.Symbol | None,
) -> tuple[SpecialCase, ...]:
    if form.rate.is_zero is not None or form.source.is_zero:
        return ()
    drift = read_result(_drift(form, variable, start, free))
    return (
        SpecialCase(
            when=Equation(read_result(form.rate), _ZERO), answer=_solved_for(function, drift)
        ),
    )


def _normal_form(function: BoundSymbol, form: LinearForm, unknown: sympy.Expr) -> Equation:
    slope = UnknownFunction(function.name, 1, Symbol(function.require_argument()))
    return Equation(slope, read_result(form.rate * unknown + form.source))


def _solved_for(function: BoundSymbol, value: Expression) -> Equation:
    return Equation(UnknownFunction(function.name, 0, Symbol(function.require_argument())), value)
