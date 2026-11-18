import json

from quantum_calculator.domain.statements import StatementSpec
from quantum_calculator.interfaces.serialization.decoding.statement_decoder import decode_statement

type SymbolDeclarations = dict[str, dict[str, str]]

LAMBDA = "\N{GREEK SMALL LETTER LAMDA}"
REAL_VARIABLE = {"role": "variable", "domain": "real", "unit": "1"}
REAL_PARAMETER = {"role": "parameter", "domain": "real", "unit": "1"}
POSITIVE_PARAMETER = {"role": "parameter", "domain": "positive", "unit": "1"}

CALCULUS: SymbolDeclarations = {
    "x": REAL_VARIABLE,
    "y": REAL_VARIABLE,
    "a": REAL_PARAMETER,
    "b": POSITIVE_PARAMETER,
}
DECAY: SymbolDeclarations = {
    "t": {"role": "variable", "domain": "real", "unit": "s"},
    "k": {"role": "parameter", "domain": "positive", "unit": "1/s"},
    "y_0": POSITIVE_PARAMETER,
    "y": {"role": "function", "domain": "real", "unit": "1", "argument": "t"},
}
KINEMATICS: SymbolDeclarations = {
    "t": {"role": "variable", "domain": "real", "unit": "s"},
    "tau": {"role": "parameter", "domain": "positive", "unit": "s"},
    "h": {"role": "parameter", "domain": "positive", "unit": "m"},
    "g": {"role": "parameter", "domain": "positive", "unit": "m/s^2"},
}
DECAY_EQUATION = "y' = -k*y"
DECAY_CONDITION = "y(0) = y_0"
DECAY_SOLUTION = "y(t) = y_0*exp(-k*t)"


def statement_document(
    statement: str, symbols: SymbolDeclarations, notation: str = "text", /, **fields: object
) -> bytes:
    document = {
        "schema_version": "1.0",
        "notation": notation,
        "statement": statement,
        "symbols": symbols,
        **fields,
    }
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


def statement_spec(
    statement: str, symbols: SymbolDeclarations, notation: str = "text", /, **fields: object
) -> StatementSpec:
    return decode_statement(statement_document(statement, symbols, notation, **fields))
