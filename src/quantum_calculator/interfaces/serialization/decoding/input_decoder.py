from collections.abc import Collection

from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.statements import StatementSpec
from quantum_calculator.interfaces.serialization.decoding.json_document import read_document
from quantum_calculator.interfaces.serialization.decoding.numerical_decoder import (
    NUMERICS_FIELD,
    decode_numerical_document,
)
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import (
    decode_problem_document,
)
from quantum_calculator.interfaces.serialization.decoding.statement_decoder import (
    STATEMENT_ONLY_FIELDS,
    decode_statement_document,
)

type InputSpec = ProblemSpec | StatementSpec | NumericalSpec

_PROBLEM = "problem"


def decode_input(raw: bytes, numerical_cards: Collection[str]) -> InputSpec:
    source, content = read_document(raw)
    if _names_a_numerical_card(content, numerical_cards):
        return decode_numerical_document(source, content)
    if STATEMENT_ONLY_FIELDS & content.keys():
        return decode_statement_document(source, content)
    return decode_problem_document(source, content)


def _names_a_numerical_card(content: dict[str, object], numerical_cards: Collection[str]) -> bool:
    problem = content.get(_PROBLEM)
    return NUMERICS_FIELD in content or (isinstance(problem, str) and problem in numerical_cards)
