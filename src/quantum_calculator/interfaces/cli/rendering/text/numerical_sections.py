from quantum_calculator.application.numerical.estimates import MAX_MEMORY_BYTES, MAX_OPERATIONS
from quantum_calculator.domain.numerical.problems import NumericalContext, NumericalProblem
from quantum_calculator.domain.numerical.report import NumericalAnswer, NumericalRunRecord
from quantum_calculator.domain.rounding import (
    ROUNDING_MODE,
    UNCERTAINTY_SIGNIFICANT_DIGITS,
    render_float,
)
from quantum_calculator.interfaces.cli.rendering.text.formatting import (
    QuantityFormatter,
    printable,
    section,
)
from quantum_calculator.interfaces.cli.rendering.text.numerical_tables import with_unit
from quantum_calculator.interfaces.cli.rendering.text.record_sections import constant_lines


def numerical_answer_lines(record: NumericalRunRecord) -> list[str]:
    digits = record.problem.context.rounding.significant_digits
    return [
        *(_answer_line(answer, digits) for answer in record.report.answers),
        f"resultado {record.report.nature.value}; {digits} algarismos significativos, "
        f"arredondamento {ROUNDING_MODE}; verificação: {record.verification.status.value}",
    ]


def numerical_problem_sections(problem: NumericalProblem) -> list[str]:
    context = problem.context
    estimate = context.estimate
    lines = section("Problema", _identification(context))
    if context.hypotheses:
        lines += section(
            "Hipóteses",
            [
                f"confirmada: {item.key} = {item.value}. {item.statement}"
                for item in context.hypotheses
            ],
        )
    lines += section(
        "Entradas interpretadas",
        [
            f"{item.label} ({item.name}): {printable(item.value)}; {printable(item.origin)}"
            for item in context.inputs
        ],
    )
    lines += section(
        "Resolução pedida",
        [f"{item.label} ({item.name}): {printable(item.value)}" for item in context.resolution],
    )
    lines += section(
        "Estimativa antes de alocar",
        [
            f"memória: {estimate.memory_bytes} bytes; operações elementares: {estimate.operations}",
            f"perfil homologado: até {MAX_MEMORY_BYTES} bytes e {MAX_OPERATIONS} operações",
        ],
    )
    return lines


def numerical_constants_section(
    record: NumericalRunRecord, numbers: QuantityFormatter
) -> list[str]:
    constants = record.problem.context.constants
    if not constants:
        return []
    return section(f"Constantes ({record.constants_edition})", constant_lines(constants, numbers))


def numerical_method_section(record: NumericalRunRecord) -> list[str]:
    method = record.plan.method
    lines = [f"método: {method.identifier} ({method.nature.value})", method.justification]
    lines += [f"{item.label} ({item.name}): {item.value}" for item in record.report.effective]
    lines += [f"aviso: {warning}" for warning in record.report.warnings]
    return section("Método e parâmetros efetivos", lines)


def _identification(context: NumericalContext) -> list[str]:
    card = context.card
    spec = context.spec
    lines = [
        f"ficha: {card.identifier} {card.version}",
        card.title,
        f"área: {card.area}; tipo: {card.problem_type}",
        *(f"domínio: {item}" for item in card.domain),
    ]
    if spec.description is not None:
        lines.append(f"descrição: {printable(spec.description)}")
    lines.append(f"entrada (sha256): {spec.source.sha256}")
    return lines


def _answer_line(answer: NumericalAnswer, significant_digits: int) -> str:
    value = with_unit(str(render_float(answer.value, significant_digits)), answer.unit)
    line = f"{answer.symbol} = {value}"
    if answer.estimate is None:
        return line
    estimate = with_unit(
        str(render_float(answer.estimate.value, UNCERTAINTY_SIGNIFICANT_DIGITS)), answer.unit
    )
    return f"{line}; erro estimado {estimate} ({answer.estimate.origin})"
