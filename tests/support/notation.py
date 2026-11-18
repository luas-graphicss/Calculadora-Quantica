from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.expressions import Equation, Expression, Statement
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import BoundSymbol, Notation, SymbolDomain, SymbolRole
from quantum_calculator.notation.reader import read_statement
from quantum_calculator.notation.rendering.structure import render_structure

LAMBDA = "\N{GREEK SMALL LETTER LAMDA}"
OMEGA = "\N{GREEK SMALL LETTER OMEGA}"

type SymbolTable = dict[str, BoundSymbol]


def declared(
    name: str,
    role: SymbolRole = SymbolRole.VARIABLE,
    argument: str | None = None,
    domain: SymbolDomain = SymbolDomain.REAL,
    dimension: Dimension | None = None,
) -> BoundSymbol:
    return BoundSymbol(name, role, domain, dimension or Dimension(), "1", argument)


def symbol_table(*symbols: BoundSymbol) -> SymbolTable:
    return {symbol.name: symbol for symbol in symbols}


SYMBOLS = symbol_table(
    declared("x"),
    declared("y"),
    declared("t"),
    declared("a", SymbolRole.PARAMETER),
    declared("b", SymbolRole.PARAMETER),
    declared("k", SymbolRole.PARAMETER),
    declared("y_0", SymbolRole.PARAMETER),
    declared(LAMBDA, SymbolRole.PARAMETER),
    declared(f"{OMEGA}_0", SymbolRole.PARAMETER),
    declared("u", SymbolRole.FUNCTION, "t"),
)


def read(notation: Notation, statement: str, symbols: SymbolTable = SYMBOLS) -> Statement:
    return read_statement(notation, statement, symbols)


def read_expression_text(statement: str, symbols: SymbolTable = SYMBOLS) -> Expression:
    tree = read(Notation.TEXT, statement, symbols)
    if isinstance(tree, Equation):
        raise TypeError(f"{statement!r} is an equation, not an expression")
    return tree


def structure_of(notation: Notation, statement: str, symbols: SymbolTable = SYMBOLS) -> str:
    return render_structure(read(notation, statement, symbols))


def refusal_or_none(
    notation: Notation, statement: str, symbols: SymbolTable = SYMBOLS
) -> StatementError | None:
    try:
        read(notation, statement, symbols)
    except StatementError as refusal:
        return refusal
    return None


def refusal_of(
    notation: Notation, statement: str, symbols: SymbolTable = SYMBOLS
) -> StatementError:
    refusal = refusal_or_none(notation, statement, symbols)
    if refusal is None:
        raise AssertionError(f"{statement!r} was accepted")
    return refusal
