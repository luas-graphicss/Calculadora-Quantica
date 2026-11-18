import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.conditions import UndefinedExpressionError, analyze_interval
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    Equation,
    Expression,
    Integral,
    Symbol,
)
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import (
    DomainCondition,
    SymbolicSolverReport,
    SymbolicStep,
)
from quantum_calculator.notation.rendering.conditions import render_condition
from quantum_calculator.solvers.symbolic.primitives import find_primitive
from quantum_calculator.solvers.symbolic.results import (
    fresh_constant,
    read_result,
    rejection,
    solution_domain,
    undefined_expression,
)

_FINITE_REGULAR_INTERVAL = (
    "um intervalo fechado sem singularidade do integrando nem da primitiva; integrais "
    "impróprias não são cobertas"
)


class AntiderivativeSolver:
    def solve(self, problem: ValidatedStatement) -> SymbolicSolverReport:
        integral = _integral_of(problem)
        builder = ExpressionBuilder(problem.symbols)
        domain = solution_domain(problem, builder, integral.body)
        variable = builder.symbol(integral.variable)
        primitive = read_result(find_primitive(builder.build(integral.body), variable))
        constant = fresh_constant(problem)
        family = BinaryOperation(BinaryOperator.ADD, primitive, Symbol(constant))
        return SymbolicSolverReport(
            answer=Equation(integral, family),
            nature=ResultNature.EXACT,
            validity=domain.validity,
            assumptions=domain.assumptions,
            special_cases=(),
            arbitrary_constants=(constant,),
            certificate=None,
            steps=(SymbolicStep("Primitiva encontrada, sem a constante de integração", primitive),),
        )


class DefiniteIntegralSolver:
    def solve(self, problem: ValidatedStatement) -> SymbolicSolverReport:
        integral = _integral_of(problem)
        if integral.bounds is None:
            raise TypeError("the fundamental theorem needs integration bounds")
        builder = ExpressionBuilder(problem.symbols)
        variable = builder.symbol(integral.variable)
        primitive = find_primitive(builder.build(integral.body), variable)
        certificate = read_result(primitive)
        assumptions = _regular_interval(builder, integral, certificate)
        upper = primitive.subs(variable, builder.build(integral.bounds.upper))
        lower = primitive.subs(variable, builder.build(integral.bounds.lower))
        value = read_result(sympy.simplify(upper - lower))
        return SymbolicSolverReport(
            answer=Equation(integral, value),
            nature=ResultNature.EXACT,
            validity=(),
            assumptions=assumptions,
            special_cases=(),
            arbitrary_constants=(),
            certificate=certificate,
            steps=(
                SymbolicStep("Primitiva contínua no intervalo de integração", certificate),
                SymbolicStep("Diferença da primitiva entre o limite superior e o inferior", value),
            ),
        )


def _integral_of(problem: ValidatedStatement) -> Integral:
    if not isinstance(problem.statement, Integral):
        raise TypeError("integration needs an integral statement")
    return problem.statement


def _regular_interval(
    builder: ExpressionBuilder, integral: Integral, primitive: Expression
) -> tuple[DomainCondition, ...]:
    if integral.bounds is None:
        raise TypeError("the fundamental theorem needs integration bounds")
    bounds = (integral.bounds.lower, integral.bounds.upper)
    try:
        analysis = analyze_interval(builder, integral, integral.body, primitive, *bounds)
    except UndefinedExpressionError as error:
        raise undefined_expression(error.condition) from error
    if analysis.singularities:
        found = "; ".join(
            f"{render_condition(singularity.condition)} falha em {singularity.location}"
            for singularity in analysis.singularities
        )
        raise rejection(
            DiagnosticCode.SINGULARITY_IN_INTERVAL,
            f"Há singularidade no intervalo de integração fechado: {found}.",
            _FINITE_REGULAR_INTERVAL,
        )
    return analysis.assumptions
