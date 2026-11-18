from collections.abc import Mapping

from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expression_traversal import (
    is_explicit,
    symbol_names,
    unknown_functions,
    walk,
)
from quantum_calculator.domain.expressions import (
    Derivative,
    DerivativeKind,
    Equation,
    Expression,
    Integral,
    SourceSpan,
    Statement,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.domain.statement_cards import StatementShape
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import BoundSymbol, SymbolRole

_EXPLICIT_EXPRESSION = "expressão só com números, símbolos, operações e funções registradas"
_CONDITION_FORM = "condição da forma y(t0) = y0, com t0 e y0 independentes da variável"
_CANDIDATE_FORM = "candidata da forma y(t) = expressão explícita, sem a própria incógnita"
_FIRST_ORDER_FORM = (
    "uma única função incógnita, no argumento declarado, com derivada de primeira ordem"
)


def statement_shape(statement: Statement) -> StatementShape | None:
    if isinstance(statement, Derivative):
        return StatementShape.DERIVATIVE
    if isinstance(statement, Integral):
        if statement.bounds is None:
            return StatementShape.ANTIDERIVATIVE
        return StatementShape.DEFINITE_INTEGRAL
    if isinstance(statement, Equation) and any(
        reference.order > 0 for reference in unknown_functions(statement)
    ):
        return StatementShape.FIRST_ORDER_ODE
    return None


def check_operator(statement: Statement, symbols: Mapping[str, BoundSymbol]) -> None:
    if isinstance(statement, Derivative):
        _check_derivative(statement, symbols)
    elif isinstance(statement, Integral):
        _check_integral(statement, symbols)


def unknown_of(equation: Statement, symbols: Mapping[str, BoundSymbol]) -> BoundSymbol:
    references = unknown_functions(equation)
    names = sorted({reference.name for reference in references})
    if len(names) != 1:
        raise StatementError(
            DiagnosticCode.OUTSIDE_COVERAGE,
            equation.span,
            f"A equação envolve mais de uma função incógnita: {', '.join(names)}.",
            _FIRST_ORDER_FORM,
        )
    function = symbols[names[0]]
    for reference in references:
        _check_reference(reference, function)
    _require_explicit_operators(equation)
    return function


def check_initial_condition(condition: Statement, function: BoundSymbol) -> Equation:
    if (
        isinstance(condition, Equation)
        and isinstance(condition.left, UnknownFunction)
        and condition.left.name == function.name
        and condition.left.order == 0
        and _is_free_of(condition.left.argument, function)
        and _is_free_of(condition.right, function)
    ):
        return condition
    raise StatementError(
        DiagnosticCode.MALFORMED_CONDITION,
        condition.span,
        f"A condição não fixa o valor de {function.name} em um ponto.",
        _CONDITION_FORM,
    )


def check_candidate(candidate: Statement, function: BoundSymbol) -> Equation:
    if (
        isinstance(candidate, Equation)
        and candidate.left == _at_declared_argument(function)
        and is_explicit(candidate.right)
    ):
        return candidate
    raise StatementError(
        DiagnosticCode.MALFORMED_CANDIDATE,
        candidate.span,
        f"A candidata não dá {function.name}({function.argument}) como expressão explícita.",
        _CANDIDATE_FORM,
    )


def _check_derivative(derivative: Derivative, symbols: Mapping[str, BoundSymbol]) -> None:
    _require_variable(derivative.variable, derivative.span, symbols)
    _require_explicit(derivative.body, "O operando da derivada")
    if derivative.kind is DerivativeKind.PARTIAL:
        return
    others = sorted(
        name
        for name in symbol_names(derivative.body)
        if name != derivative.variable and symbols[name].role is SymbolRole.VARIABLE
    )
    if others:
        listed = ", ".join(others)
        raise StatementError(
            DiagnosticCode.AMBIGUOUS_DERIVATIVE,
            derivative.span,
            f"A derivada ordinária em {derivative.variable} não diz o que acontece com "
            f"{listed}, também declarado como variável.",
            f"partial(...) para manter {listed} fixo, ou a declaração de {listed} como parâmetro",
        )


def _check_integral(integral: Integral, symbols: Mapping[str, BoundSymbol]) -> None:
    _require_variable(integral.variable, integral.span, symbols)
    _require_explicit(integral.body, "O integrando")
    if integral.bounds is None:
        return
    for bound in (integral.bounds.lower, integral.bounds.upper):
        _require_explicit(bound, "O limite de integração")
        if integral.variable in symbol_names(bound):
            raise StatementError(
                DiagnosticCode.BOUND_VARIABLE_MISUSE,
                bound.span,
                f"A variável de integração {integral.variable} é ligada e não pode aparecer "
                "nos limites.",
                f"limites que não dependam de {integral.variable}",
            )


def _check_reference(reference: UnknownFunction, function: BoundSymbol) -> None:
    if reference.order > 1:
        raise StatementError(
            DiagnosticCode.OUTSIDE_COVERAGE,
            reference.span,
            f"A derivada de ordem {reference.order} de {function.name} está fora da cobertura: "
            "só equações de primeira ordem.",
            _FIRST_ORDER_FORM,
        )
    if reference != _at_declared_argument(function, reference.order):
        raise StatementError(
            DiagnosticCode.OUTSIDE_COVERAGE,
            reference.span,
            f"Na equação, {function.name} precisa aparecer no argumento declarado "
            f"{function.argument}.",
            _FIRST_ORDER_FORM,
        )


def _require_explicit_operators(equation: Statement) -> None:
    for node in walk(equation):
        if isinstance(node, Derivative | Integral):
            raise StatementError(
                DiagnosticCode.OUTSIDE_COVERAGE,
                node.span,
                "A equação tem um operador de derivada ou de integral além da derivada da "
                "incógnita.",
                _FIRST_ORDER_FORM,
            )


def _require_variable(name: str, span: SourceSpan, symbols: Mapping[str, BoundSymbol]) -> None:
    role = symbols[name].role
    if role is not SymbolRole.VARIABLE:
        raise StatementError(
            DiagnosticCode.NOT_A_VARIABLE,
            span,
            f"{name} foi declarado como {role.value}; a derivação e a integração são em "
            "relação a uma variável.",
            'um símbolo declarado com o papel "variable"',
        )


def _require_explicit(expression: Expression, subject: str) -> None:
    for node in walk(expression):
        if isinstance(node, UnknownFunction | Derivative | Integral):
            raise StatementError(
                DiagnosticCode.OUTSIDE_COVERAGE,
                node.span,
                f"{subject} precisa ser explícito: funções incógnitas, derivadas e integrais "
                "aninhadas estão fora da cobertura.",
                _EXPLICIT_EXPRESSION,
            )


def _is_free_of(expression: Expression, function: BoundSymbol) -> bool:
    return is_explicit(expression) and function.argument not in symbol_names(expression)


def _at_declared_argument(function: BoundSymbol, order: int = 0) -> UnknownFunction:
    if function.argument is None:
        raise LookupError(f"function symbol {function.name} has no declared argument")
    return UnknownFunction(function.name, order, Symbol(function.argument))
