from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.validated_problem import BoundQuantity, ValidatedProblem
from quantum_calculator.interfaces.cli.rendering.text.formatting import (
    QuantityFormatter,
    printable,
    section,
)


def problem_sections(problem: ValidatedProblem, numbers: QuantityFormatter) -> list[str]:
    return [
        *section("Problema", _identification(problem)),
        *section("Hipóteses", _hypotheses(problem)),
        *section("Parâmetros em unidades coerentes do SI", _parameters(problem, numbers)),
    ]


def request_section(problem: ValidatedProblem, numbers: QuantityFormatter) -> list[str]:
    output = problem.output
    lines = [f"{output.rule.symbol} ({output.rule.label}) em {output.unit.symbol}"]
    model = problem.uncertainty
    if model is None:
        lines.append("incerteza: nenhuma declarada; o resultado sai com incerteza não avaliada")
    else:
        lines.append(f"incertezas-padrão declaradas, covariância {model.covariance}:")
        lines.extend(
            f"  u({problem.quantity(declared.parameter).symbol}) = "
            f"{numbers.quantity(declared.given.to_si())}"
            for declared in model.standard_uncertainties
        )
    return section("Saída pedida", lines)


def _identification(problem: ValidatedProblem) -> list[str]:
    card = problem.card
    spec = problem.spec
    lines = [f"ficha: {card.identifier} {card.version}", card.title]
    if spec.description is not None:
        lines.append(f"descrição: {printable(spec.description)}")
    lines.append(f"entrada (sha256): {spec.source.sha256}")
    return lines


def _hypotheses(problem: ValidatedProblem) -> list[str]:
    inherent = [f"da ficha: {statement}" for statement in problem.card.scope]
    confirmed = [
        f"confirmada: {item.key} = {item.value}. {item.statement}" for item in problem.hypotheses
    ]
    return inherent + confirmed


def _parameters(problem: ValidatedProblem, numbers: QuantityFormatter) -> list[str]:
    quantities = [_quantity_line(bound, numbers) for bound in problem.quantities]
    counts = [f"{bound.symbol} = {bound.value}" for bound in problem.counts]
    return quantities + counts


def _quantity_line(bound: BoundQuantity, numbers: QuantityFormatter) -> str:
    value = numbers.quantity(bound.quantity)
    if isinstance(bound.origin, PhysicalConstant):
        return f"{bound.symbol} = {value}; constante {bound.origin.identifier} do catálogo"
    given = bound.origin
    literal = printable(given.number.literal)
    return f"{bound.symbol} = {value}; entrada: {literal} {given.unit.symbol}"
