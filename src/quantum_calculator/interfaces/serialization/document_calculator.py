from collections.abc import Callable

from quantum_calculator.composition import Calculator
from quantum_calculator.domain.diagnostics import ProblemRejectedError
from quantum_calculator.domain.execution import CancellationSignal
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.statements import StatementSpec
from quantum_calculator.interfaces.serialization.decoding.input_decoder import (
    InputSpec,
    decode_input,
)
from quantum_calculator.interfaces.serialization.encoding.documents import (
    DocumentEncoder,
    encode_rejection,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject
from quantum_calculator.interfaces.serialization.encoding.numerical_documents import (
    NumericalDocumentEncoder,
)
from quantum_calculator.interfaces.serialization.encoding.statement_documents import (
    StatementDocumentEncoder,
)


class DocumentCalculator:
    def __init__(self, calculator_for: Callable[[float], Calculator]) -> None:
        self._calculator_for = calculator_for

    def interpret(self, source: bytes, wall_seconds: float) -> JsonObject:
        calculator = self._calculator_for(wall_seconds)
        try:
            return _reviewed(calculator, decode_input(source, calculator.numerical_cards))
        except ProblemRejectedError as rejection:
            return encode_rejection(rejection)

    def calculate(
        self, source: bytes, wall_seconds: float, cancellation: CancellationSignal
    ) -> JsonObject:
        calculator = self._calculator_for(wall_seconds)
        try:
            spec = decode_input(source, calculator.numerical_cards)
            return _solved(calculator, spec, cancellation)
        except ProblemRejectedError as rejection:
            return encode_rejection(rejection)


def _reviewed(calculator: Calculator, spec: InputSpec) -> JsonObject:
    if isinstance(spec, NumericalSpec):
        numerical = calculator.review_numerical.execute(spec)
        return NumericalDocumentEncoder(calculator.units).validation(
            numerical.problem, numerical.plan
        )
    if isinstance(spec, StatementSpec):
        statement = calculator.review_statement.execute(spec)
        return StatementDocumentEncoder(calculator.units).validation(
            statement.problem, statement.plan
        )
    review = calculator.review_problem.execute(spec)
    return DocumentEncoder(calculator.units).validation(review.problem, review.plan)


def _solved(
    calculator: Calculator, spec: InputSpec, cancellation: CancellationSignal
) -> JsonObject:
    if isinstance(spec, NumericalSpec):
        return NumericalDocumentEncoder(calculator.units).run_record(
            calculator.solve_numerical.execute(spec, cancellation)
        )
    if isinstance(spec, StatementSpec):
        return StatementDocumentEncoder(calculator.units).run_record(
            calculator.solve_statement.execute(spec, cancellation)
        )
    return DocumentEncoder(calculator.units).run_record(calculator.solve_problem.execute(spec))
