from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start: int
    end: int


NO_SPAN = SourceSpan(0, 0)


class BinaryOperator(StrEnum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    POWER = "power"


class ElementaryFunction(StrEnum):
    SIN = "sin"
    COS = "cos"
    TAN = "tan"
    EXP = "exp"
    LN = "ln"
    SQRT = "sqrt"
    ABS = "abs"


class DerivativeKind(StrEnum):
    ORDINARY = "ordinary"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class Number:
    value: Fraction
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class Pi:
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class Symbol:
    name: str
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class Negation:
    operand: "Expression"
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class BinaryOperation:
    operator: BinaryOperator
    left: "Expression"
    right: "Expression"
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class FunctionCall:
    function: ElementaryFunction
    argument: "Expression"
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class UnknownFunction:
    name: str
    order: int
    argument: "Expression"
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class Derivative:
    kind: DerivativeKind
    body: "Expression"
    variable: str
    order: int
    span: SourceSpan = field(default=NO_SPAN, compare=False)


@dataclass(frozen=True, slots=True)
class IntegrationBounds:
    lower: "Expression"
    upper: "Expression"


@dataclass(frozen=True, slots=True)
class Integral:
    body: "Expression"
    variable: str
    bounds: IntegrationBounds | None
    span: SourceSpan = field(default=NO_SPAN, compare=False)


type Expression = (
    Number
    | Pi
    | Symbol
    | Negation
    | BinaryOperation
    | FunctionCall
    | UnknownFunction
    | Derivative
    | Integral
)


@dataclass(frozen=True, slots=True)
class Equation:
    left: Expression
    right: Expression
    span: SourceSpan = field(default=NO_SPAN, compare=False)


type Statement = Expression | Equation
