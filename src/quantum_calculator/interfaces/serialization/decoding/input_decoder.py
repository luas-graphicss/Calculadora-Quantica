from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.statements import StatementSpec
from quantum_calculator.interfaces.serialization.decoding.json_document import read_document
from quantum_calculator.interfaces.serialization.decoding.problem_decoder import (
    decode_problem_document,
)
from quantum_calculator.interfaces.serialization.decoding.statement_decoder import (
    STATEMENT_ONLY_FIELDS,
    decode_statement_document,
)

type InputSpec = ProblemSpec | StatementSpec


def decode_input(raw: bytes) -> InputSpec:
    source, content = read_document(raw)
    if STATEMENT_ONLY_FIELDS & content.keys():
        return decode_statement_document(source, content)
    return decode_problem_document(source, content)
