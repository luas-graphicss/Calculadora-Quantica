from collections.abc import Mapping
from dataclasses import dataclass

from quantum_calculator.application.statements.shape_rules import check_initial_condition
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expression_traversal import unknown_functions, walk
from quantum_calculator.domain.expressions import (
    Derivative,
    Equation,
    Expression,
    Integral,
    Statement,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import BoundSymbol

EXPLICIT_FORM = "uma equação por função, na forma y' = f(t, y, ...), com o lado direito explícito"
CONDITION_FORM = "uma condição por função, todas no mesmo instante, como y(0) = 1"


@dataclass(frozen=True, slots=True)
class ExplicitEquation:
    function: BoundSymbol
    derivative: Expression


@dataclass(frozen=True, slots=True)
class InitialCondition:
    function: BoundSymbol
    instant: Expression
    value: Expression


def explicit_equation(statement: Statement, symbols: Mapping[str, BoundSymbol]) -> ExplicitEquation:
    if not (
        isinstance(statement, Equation)
        and isinstance(statement.left, UnknownFunction)
        and statement.left.order == 1
    ):
        raise StatementError(
            DiagnosticCode.OUTSIDE_COVERAGE,
            statement.span,
            "A equação não isola à esquerda a derivada de primeira ordem de uma função.",
            EXPLICIT_FORM,
        )
    for node in walk(statement.right):
        if isinstance(node, Derivative | Integral) or (
            isinstance(node, UnknownFunction) and node.order != 0
        ):
            raise StatementError(
                DiagnosticCode.OUTSIDE_COVERAGE,
                node.span,
                "O lado direito precisa ser explícito: sem derivadas nem integrais.",
                EXPLICIT_FORM,
            )
    for reference in unknown_functions(statement):
        declared = symbols[reference.name]
        if reference.argument != Symbol(declared.require_argument()):
            raise StatementError(
                DiagnosticCode.OUTSIDE_COVERAGE,
                reference.span,
                f"No sistema, {reference.name} precisa aparecer no argumento declarado "
                f"{declared.argument}.",
                EXPLICIT_FORM,
            )
    return ExplicitEquation(symbols[statement.left.name], statement.right)


def initial_condition(
    statement: Statement, functions: Mapping[str, BoundSymbol]
) -> InitialCondition:
    if (
        isinstance(statement, Equation)
        and isinstance(statement.left, UnknownFunction)
        and statement.left.name in functions
    ):
        function = functions[statement.left.name]
        condition = check_initial_condition(statement, function)
        return InitialCondition(function, statement.left.argument, condition.right)
    raise StatementError(
        DiagnosticCode.MALFORMED_CONDITION,
        statement.span,
        "A condição não fixa em um ponto o valor de uma função do sistema.",
        CONDITION_FORM,
    )
