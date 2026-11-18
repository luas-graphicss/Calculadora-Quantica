from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial

from quantum_calculator.application.statements.field_reader import FieldReader, ReadField
from quantum_calculator.application.statements.shape_rules import (
    check_candidate,
    check_initial_condition,
    check_operator,
    unknown_of,
)
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.expression_dimensions import DimensionAnalyzer
from quantum_calculator.domain.expressions import Equation
from quantum_calculator.domain.statement_cards import StatementShape
from quantum_calculator.domain.statements import BoundSymbol

_SINGLE_CONDITION = "uma única condição inicial, como y(0) = y_0"


@dataclass(frozen=True, slots=True)
class StatementSemantics:
    result_dimension: Dimension
    conditions: tuple[Equation, ...]
    candidate: Equation | None


class SemanticChecker:
    def __init__(self, symbols: Mapping[str, BoundSymbol], reader: FieldReader) -> None:
        self._symbols = symbols
        self._reader = reader
        self._dimensions = DimensionAnalyzer(symbols)

    def check(
        self,
        shape: StatementShape,
        statement: ReadField,
        conditions: tuple[ReadField, ...],
        candidate: ReadField | None,
    ) -> StatementSemantics | None:
        if shape is StatementShape.FIRST_ORDER_ODE:
            return self._differential_equation(statement, conditions, candidate)
        self._reader.check(statement, partial(check_operator, statement.statement, self._symbols))
        dimension = self._dimension_of(statement)
        return None if dimension is None else StatementSemantics(dimension, (), None)

    def _differential_equation(
        self,
        statement: ReadField,
        conditions: tuple[ReadField, ...],
        candidate: ReadField | None,
    ) -> StatementSemantics | None:
        function = self._reader.check(
            statement, partial(unknown_of, statement.statement, self._symbols)
        )
        self._dimension_of(statement)
        if function is None:
            return None
        checked_conditions = [self._condition(condition, function) for condition in conditions[:1]]
        for surplus in conditions[1:]:
            self._reader.report(
                surplus,
                DiagnosticCode.MALFORMED_CONDITION,
                "Uma equação de primeira ordem aceita uma única condição inicial.",
                _SINGLE_CONDITION,
            )
        checked_candidate = None
        if candidate is not None:
            checked_candidate = self._reader.check(
                candidate, partial(check_candidate, candidate.statement, function)
            )
            self._dimension_of(candidate)
        return StatementSemantics(
            result_dimension=function.dimension,
            conditions=tuple(checked for checked in checked_conditions if checked is not None),
            candidate=checked_candidate,
        )

    def _condition(self, condition: ReadField, function: BoundSymbol) -> Equation | None:
        self._dimension_of(condition)
        return self._reader.check(
            condition, partial(check_initial_condition, condition.statement, function)
        )

    def _dimension_of(self, field: ReadField) -> Dimension | None:
        return self._reader.check(field, partial(self._dimensions.check, field.statement))
