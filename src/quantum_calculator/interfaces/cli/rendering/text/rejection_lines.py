from quantum_calculator.domain.diagnostics import ProblemRejectedError, SourceExcerpt
from quantum_calculator.interfaces.cli.rendering.text.formatting import printable

_INDENT = "    "
_EXCERPT_LABEL = "trecho: "
_MARKER = "^"


def rejection_lines(rejection: ProblemRejectedError) -> list[str]:
    lines = [f"Entrada recusada ({rejection.category.value})"]
    for item in rejection.diagnostics:
        lines.append(f"  {printable(item.pointer) or '/'} [{item.code.value}]")
        lines.append(f"{_INDENT}{printable(item.message)}")
        lines.append(f"{_INDENT}esperado: {printable(item.expected)}")
        if item.excerpt is not None:
            lines.extend(_excerpt_lines(item.excerpt))
    return lines


def _excerpt_lines(excerpt: SourceExcerpt) -> list[str]:
    offset = " " * (len(_EXCERPT_LABEL) + excerpt.start)
    marker = _MARKER * max(excerpt.end - excerpt.start, 1)
    return [
        f"{_INDENT}{_EXCERPT_LABEL}{printable(excerpt.text)}",
        f"{_INDENT}{offset}{marker}",
    ]
