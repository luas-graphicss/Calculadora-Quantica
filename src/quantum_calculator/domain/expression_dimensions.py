from collections.abc import Mapping

from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.dimensions import DIMENSIONLESS, Dimension
from quantum_calculator.domain.expressions import (
    BinaryOperation,
    BinaryOperator,
    Derivative,
    ElementaryFunction,
    Equation,
    Expression,
    FunctionCall,
    Integral,
    Negation,
    Number,
    Pi,
    SourceSpan,
    Statement,
    Symbol,
    UnknownFunction,
)
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import BoundSymbol

_DIMENSIONLESS_LABEL = "adimensional"
_DIMENSIONLESS_ARGUMENT = (
    "argumento adimensional, por exemplo a grandeza dividida por uma escala de mesma unidade"
)
_SUMS = (BinaryOperator.ADD, BinaryOperator.SUBTRACT)


def describe_dimension(dimension: Dimension) -> str:
    return _DIMENSIONLESS_LABEL if dimension == DIMENSIONLESS else dimension.base_si_unit()


class DimensionAnalyzer:
    def __init__(self, symbols: Mapping[str, BoundSymbol]) -> None:
        self._symbols = symbols

    def check(self, statement: Statement) -> Dimension:
        if isinstance(statement, Equation):
            left = self._dimension_of(statement.left)
            right = self._dimension_of(statement.right)
            return _common(statement.left, left, statement.right, right, statement.span)
        return self._dimension_of(statement)

    def _dimension_of(self, expression: Expression) -> Dimension:
        match expression:
            case Number() | Pi():
                return DIMENSIONLESS
            case Symbol():
                return self._symbols[expression.name].dimension
            case Negation():
                return self._dimension_of(expression.operand)
            case BinaryOperation():
                return self._operation(expression)
            case FunctionCall():
                return self._function(expression)
            case UnknownFunction():
                return self._unknown_function(expression)
            case Derivative():
                variable = self._symbols[expression.variable].dimension
                return self._dimension_of(expression.body) / variable**expression.order
            case Integral():
                return self._integral(expression)

    def _operation(self, operation: BinaryOperation) -> Dimension:
        left = self._dimension_of(operation.left)
        right = self._dimension_of(operation.right)
        if operation.operator in _SUMS:
            return _common(operation.left, left, operation.right, right, operation.span)
        if operation.operator is BinaryOperator.MULTIPLY:
            return left * right
        if operation.operator is BinaryOperator.DIVIDE:
            return left / right
        return _power(operation, left, right)

    def _function(self, call: FunctionCall) -> Dimension:
        argument = self._dimension_of(call.argument)
        if call.function is ElementaryFunction.ABS:
            return argument
        if call.function is ElementaryFunction.SQRT:
            return _square_root(call, argument)
        if argument != DIMENSIONLESS:
            raise StatementError(
                DiagnosticCode.DIMENSIONAL_ARGUMENT,
                call.argument.span,
                f"O argumento de {call.function.value} tem dimensão "
                f"{describe_dimension(argument)}; funções transcendentais exigem argumento "
                "adimensional.",
                _DIMENSIONLESS_ARGUMENT,
            )
        return DIMENSIONLESS

    def _unknown_function(self, reference: UnknownFunction) -> Dimension:
        function = self._symbols[reference.name]
        if function.argument is None:
            raise LookupError(f"function symbol {reference.name} has no declared argument")
        declared = self._symbols[function.argument].dimension
        given = self._dimension_of(reference.argument)
        if given != declared and not _is_zero(reference.argument):
            raise StatementError(
                DiagnosticCode.DIMENSION_MISMATCH,
                reference.argument.span,
                f"O argumento de {reference.name} tem dimensão {describe_dimension(given)}, mas "
                f"{function.argument} foi declarado com {describe_dimension(declared)}.",
                f"argumento com dimensão {describe_dimension(declared)}",
            )
        return function.dimension / declared**reference.order

    def _integral(self, integral: Integral) -> Dimension:
        variable = self._symbols[integral.variable].dimension
        body = self._dimension_of(integral.body)
        if integral.bounds is not None:
            for bound in (integral.bounds.lower, integral.bounds.upper):
                given = self._dimension_of(bound)
                if given != variable and not _is_zero(bound):
                    raise StatementError(
                        DiagnosticCode.DIMENSION_MISMATCH,
                        bound.span,
                        f"O limite de integração tem dimensão {describe_dimension(given)}, mas "
                        f"{integral.variable} tem {describe_dimension(variable)}.",
                        f"limite com dimensão {describe_dimension(variable)}",
                    )
        return body * variable


def _power(operation: BinaryOperation, base: Dimension, exponent: Dimension) -> Dimension:
    if exponent != DIMENSIONLESS:
        raise StatementError(
            DiagnosticCode.DIMENSIONAL_ARGUMENT,
            operation.right.span,
            f"O expoente tem dimensão {describe_dimension(exponent)}.",
            "expoente adimensional",
        )
    if base == DIMENSIONLESS:
        return DIMENSIONLESS
    power = _integer_literal(operation.right)
    if power is None:
        raise StatementError(
            DiagnosticCode.DIMENSIONAL_ARGUMENT,
            operation.span,
            f"A base tem dimensão {describe_dimension(base)} e o expoente não é um inteiro "
            "literal, então a dimensão do resultado não fica definida.",
            "expoente inteiro literal, ou base adimensional",
        )
    return base**power


def _square_root(call: FunctionCall, argument: Dimension) -> Dimension:
    exponents = (argument.mass, argument.length, argument.time)
    if any(exponent % 2 for exponent in exponents):
        raise StatementError(
            DiagnosticCode.DIMENSIONAL_ARGUMENT,
            call.argument.span,
            f"A raiz quadrada de uma grandeza de dimensão {describe_dimension(argument)} não "
            "tem expoentes inteiros.",
            "argumento cuja dimensão tenha expoentes pares",
        )
    return Dimension(mass=argument.mass // 2, length=argument.length // 2, time=argument.time // 2)


def _common(
    left_node: Expression,
    left: Dimension,
    right_node: Expression,
    right: Dimension,
    span: SourceSpan,
) -> Dimension:
    if _is_zero(left_node):
        return right
    if left == right or _is_zero(right_node):
        return left
    raise StatementError(
        DiagnosticCode.DIMENSION_MISMATCH,
        span,
        f"Os dois lados têm dimensões diferentes: {describe_dimension(left)} e "
        f"{describe_dimension(right)}.",
        "termos com a mesma dimensão",
    )


def _is_zero(expression: Expression) -> bool:
    return isinstance(expression, Number) and expression.value == 0


def _integer_literal(expression: Expression) -> int | None:
    if isinstance(expression, Negation):
        magnitude = _integer_literal(expression.operand)
        return None if magnitude is None else -magnitude
    if isinstance(expression, Number) and expression.value.denominator == 1:
        return expression.value.numerator
    return None
