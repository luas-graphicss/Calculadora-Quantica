from quantum_calculator.domain.rounding import ROUNDING_MODE, render_decimal
from quantum_calculator.domain.run_record import RunRecord
from quantum_calculator.interfaces.cli.rendering.text.formatting import QuantityFormatter, section
from quantum_calculator.interfaces.serialization.encoding.display import (
    NOT_EVALUATED_REASON,
    displayed_relative_uncertainty,
    displayed_standard_uncertainty,
    displayed_value,
)


def answer_lines(record: RunRecord) -> list[str]:
    output = record.problem.output
    digits = record.plan.rounding.significant_digits
    value = render_decimal(displayed_value(record), digits).decimal
    return [
        f"{output.rule.symbol} = {value} {output.unit.symbol}",
        f"resultado {record.report.nature.value}; {digits} algarismos significativos, "
        f"arredondamento {ROUNDING_MODE}; verificação: {record.verification.status.value}",
    ]


def constants_section(record: RunRecord, numbers: QuantityFormatter) -> list[str]:
    lines = []
    for constant in record.constants:
        uncertainty = constant.standard_uncertainty
        nature = (
            "exata"
            if uncertainty is None
            else f"medida, u = {numbers.exact(uncertainty, numbers.unit_of(constant.value))}"
        )
        value = numbers.quantity(constant.value)
        lines.append(f"{constant.symbol} = {value}; {nature}; {constant.source}")
    return section(f"Constantes ({record.constants_edition})", lines)


def calculation_section(record: RunRecord, numbers: QuantityFormatter) -> list[str]:
    method = record.plan.method
    output = record.problem.output
    lines = [f"método: {method.identifier} ({method.nature.value})", method.justification]
    for index, step in enumerate(record.report.steps, start=1):
        value = "" if step.value is None else f" = {numbers.quantity(step.value)}"
        lines.append(f"{index}. {step.description}: {step.expression}{value}")
    factor_unit = f"{numbers.unit_of(record.report.value)}/{output.unit.symbol}"
    factor = numbers.exact(output.unit.si_factor, factor_unit)
    lines.append(
        f"{len(record.report.steps) + 1}. Conversão para {output.unit.symbol}: divisão por {factor}"
    )
    return section("Memória de cálculo", lines)


def uncertainty_section(record: RunRecord, numbers: QuantityFormatter) -> list[str]:
    evaluation = record.report.uncertainty
    if evaluation is None:
        return section("Incerteza", [f"não avaliada. {NOT_EVALUATED_REASON}"])
    output = record.problem.output
    digits = record.plan.rounding.significant_digits
    lines = [
        f"u({output.rule.symbol}) = {displayed_standard_uncertainty(record, evaluation)} "
        f"{output.unit.symbol}; relativa {displayed_relative_uncertainty(record, evaluation)}",
        f"propagação linear de primeira ordem, covariância {evaluation.covariance}",
    ]
    lines.extend(
        f"{item.symbol}: sensibilidade {numbers.quantity(item.sensitivity, digits)}; "
        f"u = {numbers.quantity(item.standard_uncertainty)}"
        for item in evaluation.contributions
    )
    return section("Incerteza", lines)
