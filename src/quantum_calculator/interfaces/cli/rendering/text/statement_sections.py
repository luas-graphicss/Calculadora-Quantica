from quantum_calculator.domain.dimensions import DIMENSIONLESS
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.statements import BoundSymbol, CardSelection, ValidatedStatement
from quantum_calculator.interfaces.cli.rendering.text.formatting import printable, section
from quantum_calculator.notation.rendering.latex import render_latex
from quantum_calculator.notation.rendering.structure import render_structure
from quantum_calculator.notation.rendering.text import render_text

_SELECTIONS = {
    CardSelection.CONFIRMED: "confirmada na entrada",
    CardSelection.SUGGESTED: "sugerida por ser a única compatível",
}


def statement_sections(problem: ValidatedStatement) -> list[str]:
    return [
        *section("Leitura", _reading(problem)),
        *section("Símbolos", [_symbol_line(symbol) for symbol in problem.symbols]),
        *_given_sections(problem),
        *section("Ficha", _card(problem)),
    ]


def result_unit(problem: ValidatedStatement, units: UnitRegistry) -> str:
    if problem.result_dimension == DIMENSIONLESS:
        return "adimensional"
    return f"unidade coerente do SI: {units.coherent_symbol(problem.result_dimension)}"


def _reading(problem: ValidatedStatement) -> list[str]:
    statement = problem.statement
    return [
        f"texto: {render_text(statement)}",
        f"LaTeX: {render_latex(statement)}",
        f"árvore: {render_structure(statement)}",
        f"entrada ({problem.notation.value}): {printable(problem.spec.statement)}",
    ]


def _symbol_line(symbol: BoundSymbol) -> str:
    role = symbol.role.value
    if symbol.argument is not None:
        role = f"{role} de {symbol.argument}"
    return f"{symbol.name}: {role}, domínio {symbol.domain.value}, unidade {printable(symbol.unit)}"


def _given_sections(problem: ValidatedStatement) -> list[str]:
    lines: list[str] = []
    if problem.conditions:
        lines += section("Condições", [render_text(condition) for condition in problem.conditions])
    if problem.candidate is not None:
        lines += section("Candidata", [render_text(problem.candidate)])
    return lines


def _card(problem: ValidatedStatement) -> list[str]:
    card = problem.card
    spec = problem.spec
    lines = [
        f"{card.identifier} {card.version} ({_SELECTIONS[problem.selection]})",
        card.title,
        f"área: {card.area}; tipo: {card.problem_type}",
        *(f"domínio: {item}" for item in card.domain),
    ]
    if problem.selection is CardSelection.SUGGESTED:
        lines.append(f'para confirmar, declare "problem": "{card.identifier}" na entrada')
    if spec.description is not None:
        lines.append(f"descrição: {printable(spec.description)}")
    lines.append(f"entrada (sha256): {spec.source.sha256}")
    return lines
