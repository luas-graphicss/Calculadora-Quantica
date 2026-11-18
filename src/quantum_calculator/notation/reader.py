from collections.abc import Callable, Mapping, Sequence

from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expression_traversal import node_count
from quantum_calculator.domain.expressions import SourceSpan, Statement
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import BoundSymbol, Notation
from quantum_calculator.notation.grammar import StatementParser
from quantum_calculator.notation.latex.lexer import tokenize_latex
from quantum_calculator.notation.latex.parser import LatexStatementParser
from quantum_calculator.notation.limits import MAX_NODE_COUNT, MAX_STATEMENT_LENGTH
from quantum_calculator.notation.text.lexer import tokenize_text
from quantum_calculator.notation.text.parser import TextStatementParser
from quantum_calculator.notation.tokens import Token

type _Tokenizer = Callable[[str], tuple[Token, ...]]
type _ParserFactory = Callable[[Sequence[Token], Mapping[str, BoundSymbol]], StatementParser]

_READERS: dict[Notation, tuple[_Tokenizer, _ParserFactory]] = {
    Notation.TEXT: (tokenize_text, TextStatementParser),
    Notation.LATEX: (tokenize_latex, LatexStatementParser),
}


def read_statement(notation: Notation, text: str, symbols: Mapping[str, BoundSymbol]) -> Statement:
    if len(text) > MAX_STATEMENT_LENGTH:
        raise StatementError(
            DiagnosticCode.STATEMENT_TOO_LONG,
            SourceSpan(MAX_STATEMENT_LENGTH, len(text)),
            f"O enunciado tem {len(text)} caracteres.",
            f"até {MAX_STATEMENT_LENGTH} caracteres",
        )
    tokenize, build_parser = _READERS[notation]
    statement = build_parser(tokenize(text), symbols).parse()
    size = node_count(statement)
    if size > MAX_NODE_COUNT:
        raise StatementError(
            DiagnosticCode.EXPRESSION_TOO_LARGE,
            SourceSpan(0, len(text)),
            f"A expressão tem {size} nós.",
            f"até {MAX_NODE_COUNT} nós na árvore da expressão",
        )
    return statement
