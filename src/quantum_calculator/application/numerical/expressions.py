from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.application.statements.field_reader import FieldReader, ReadField
from quantum_calculator.application.statements.symbols import SymbolBinder
from quantum_calculator.application.statements.unit_expressions import measure_of_unit
from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.domain.expression_traversal import symbol_names
from quantum_calculator.domain.expressions import Expression
from quantum_calculator.domain.numerical.problems import InterpretedInput, SymbolValue
from quantum_calculator.domain.numerical.spec import SymbolInput
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.rounding import MAX_SIGNIFICANT_DIGITS, render_decimal
from quantum_calculator.domain.statements import BoundSymbol, Notation, SymbolDomain, SymbolRole
from quantum_calculator.notation.rendering.text import render_text
from quantum_calculator.notation.vocabulary import canonical_symbol_name

_SYMBOLS = "symbols"
_VALUE = "value"
_NOTATION = "notation"
_DIMENSIONLESS = "1"
_VALUED_SYMBOLS = "todo símbolo além da variável independente declarado como parâmetro com valor"
_DOMAIN_RULES: dict[SymbolDomain, tuple[Callable[[Fraction], bool], str]] = {
    SymbolDomain.REAL: (lambda _value: True, "qualquer número real"),
    SymbolDomain.POSITIVE: (lambda value: value > 0, "valor maior que zero"),
    SymbolDomain.NEGATIVE: (lambda value: value < 0, "valor menor que zero"),
    SymbolDomain.NONNEGATIVE: (lambda value: value >= 0, "valor maior ou igual a zero"),
    SymbolDomain.NONZERO: (lambda value: value != 0, "valor diferente de zero"),
}


@dataclass(frozen=True, slots=True)
class BoundExpressions:
    notation: Notation
    symbols: dict[str, BoundSymbol]
    values: tuple[SymbolValue, ...]
    inputs: tuple[InterpretedInput, ...]
    reader: FieldReader

    @property
    def value_by_name(self) -> dict[str, float]:
        return {item.name: item.value for item in self.values}

    def describe(self, name: str, label: str, field: ReadField) -> InterpretedInput:
        return InterpretedInput(
            name,
            label,
            render_text(field.statement),
            f"entrada ({self.notation.value}): {field.text}",
        )

    def require_values(
        self, field: ReadField, expression: Expression, variable: str | None
    ) -> bool:
        valued = self.value_by_name
        missing = sorted(
            name for name in symbol_names(expression) if name != variable and name not in valued
        )
        if missing:
            self.reader.report(
                field,
                DiagnosticCode.OUTSIDE_COVERAGE,
                f"{', '.join(missing)} não tem valor numérico: só a variável independente e "
                "parâmetros com valor entram em um cálculo numérico.",
                _VALUED_SYMBOLS,
            )
        return not missing


def describe_interval(lower: float, upper: float, unit: str) -> str:
    extent = f"de {lower!r} a {upper!r}"
    return f"{extent}, adimensional" if unit == _DIMENSIONLESS else f"{extent} {unit}"


class ExpressionBinder:
    def __init__(self, units: UnitRegistry) -> None:
        self._units = units
        self._symbols = SymbolBinder(units)

    def bind(self, request: ValidationRequest) -> BoundExpressions | None:
        spec = request.spec
        if spec.notation is None or spec.symbols is None:
            return None
        reported = len(request.diagnostics)
        notation = _notation(request, spec.notation)
        symbols = self._symbols.bind(
            tuple(symbol.declaration for symbol in spec.symbols), request.diagnostics
        )
        if notation is None or len(request.diagnostics) > reported:
            return None
        valued = [self._value(request, given, symbols) for given in spec.symbols]
        if len(request.diagnostics) > reported:
            return None
        parameters = [item for item in valued if item is not None]
        return BoundExpressions(
            notation=notation,
            symbols=symbols,
            values=tuple(value for value, _ in parameters),
            inputs=tuple(described for _, described in parameters),
            reader=FieldReader(notation, symbols, request.diagnostics),
        )

    def _value(
        self, request: ValidationRequest, given: SymbolInput, symbols: dict[str, BoundSymbol]
    ) -> tuple[SymbolValue, InterpretedInput] | None:
        declared = given.declaration
        symbol = symbols[canonical_symbol_name(declared.name) or declared.name]
        pointer = pointer_to(_SYMBOLS, declared.name, _VALUE)
        if symbol.role is not SymbolRole.PARAMETER:
            if given.value is not None:
                request.refuse(
                    DiagnosticCode.UNEXPECTED_FIELD,
                    pointer,
                    f"Só um parâmetro recebe valor numérico; {quote_user_text(declared.name)} "
                    f"foi declarado como {symbol.role.value}.",
                    'nenhum campo "value" neste símbolo',
                )
            return None
        if given.value is None:
            request.refuse(
                DiagnosticCode.MISSING_FIELD,
                pointer,
                f"O parâmetro {quote_user_text(declared.name)} não tem valor numérico: um "
                "cálculo numérico precisa do valor de todos os parâmetros.",
                f"número na unidade declarada, {declared.unit}",
            )
            return None
        accepts, expected = _DOMAIN_RULES[symbol.domain]
        if not accepts(given.value.value):
            request.refuse(
                DiagnosticCode.NUMBER_OUT_OF_RANGE,
                pointer,
                f"O valor {quote_user_text(given.value.literal)} não está no domínio "
                f"{symbol.domain.value} declarado para {symbol.name}.",
                expected,
            )
            return None
        magnitude = given.value.value * measure_of_unit(declared.unit, self._units).si_factor
        shown = render_decimal(magnitude, MAX_SIGNIFICANT_DIGITS).decimal
        unit = self._units.coherent_symbol(symbol.dimension)
        return (
            SymbolValue(symbol.name, float(magnitude)),
            InterpretedInput(
                symbol.name,
                f"parâmetro {symbol.name}",
                f"{shown} {unit}",
                f"entrada: {given.value.literal} {declared.unit}",
            ),
        )


def _notation(request: ValidationRequest, given: str) -> Notation | None:
    for notation in Notation:
        if notation.value == given:
            return notation
    request.refuse(
        DiagnosticCode.UNKNOWN_OPTION,
        pointer_to(_NOTATION),
        f"{quote_user_text(given)} não é uma notação aceita.",
        f"uma destas notações: {', '.join(notation.value for notation in Notation)}",
    )
    return None
