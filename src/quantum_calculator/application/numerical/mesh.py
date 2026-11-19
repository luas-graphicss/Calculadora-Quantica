from quantum_calculator.application.numerical.limits import REFINEMENT_DIVISOR
from quantum_calculator.application.numerical.settings import SettingsReader
from quantum_calculator.domain.diagnostics import DiagnosticCode


def check_refinable(settings: SettingsReader, name: str, label: str, count: int) -> None:
    if count % REFINEMENT_DIVISOR:
        settings.refuse(
            name,
            DiagnosticCode.NUMBER_OUT_OF_RANGE,
            f"{label.capitalize()} deve ser múltiplo de {REFINEMENT_DIVISOR}: o estudo de "
            "refinamento repete o cálculo com um quarto e com a metade desse número.",
            f"múltiplo de {REFINEMENT_DIVISOR}",
        )


def check_resolved_levels(settings: SettingsReader, subintervals: int, levels: int) -> None:
    coarsest = subintervals // REFINEMENT_DIVISOR
    if levels >= coarsest:
        settings.refuse(
            "levels",
            DiagnosticCode.NUMBER_OUT_OF_RANGE,
            f"A malha mais grossa do refinamento, com {coarsest} subintervalos, não comporta "
            f"{levels} níveis.",
            f"menos de {coarsest} níveis, ou uma malha mais fina",
        )


def check_saved_instants(settings: SettingsReader, steps: int, samples: int) -> None:
    if steps % (samples - 1):
        settings.refuse(
            "samples",
            DiagnosticCode.NUMBER_OUT_OF_RANGE,
            f"{samples} instantes salvos não dividem {steps} passos em trechos iguais.",
            "um número de instantes cujo antecessor divida o número de passos",
        )
