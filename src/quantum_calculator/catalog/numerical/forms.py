from quantum_calculator.catalog.numerical.discrete_schrodinger import (
    OSCILLATOR_TRUNCATED_SPECTRUM,
    WELL_DISCRETE_SPECTRUM,
    WELL_TIME_EVOLUTION,
)
from quantum_calculator.catalog.numerical.finite_basis import PROJECTIVE_MEASUREMENT
from quantum_calculator.catalog.numerical.initial_value import EXPLICIT_RUNGE_KUTTA
from quantum_calculator.catalog.numerical.quadrature import ADAPTIVE_QUADRATURE
from quantum_calculator.domain.dimensions import ENERGY
from quantum_calculator.domain.numerical.cards import InputSection, NumericalFamily
from quantum_calculator.domain.workbench.forms import ArrayField, Presence, SettingField

_SUBINTERVALS = SettingField("subintervals", "subintervalos da malha uniforme")
_LEVELS = SettingField("levels", "níveis pedidos, a partir do fundamental")

NUMERICAL_SETTINGS = {
    ADAPTIVE_QUADRATURE.identifier: (
        SettingField(
            "absolute_tolerance", "tolerância absoluta, na unidade coerente do SI do resultado"
        ),
        SettingField("relative_tolerance", "tolerância relativa"),
        SettingField("subdivision_limit", "limite de subdivisões do intervalo"),
    ),
    EXPLICIT_RUNGE_KUTTA.identifier: (
        SettingField("end", "valor final da variável independente, na unidade declarada"),
        SettingField("samples", "instantes uniformes da trajetória"),
        SettingField("relative_tolerance", "tolerância relativa por passo"),
        SettingField(
            "absolute_tolerance",
            "tolerância absoluta por passo, na unidade coerente do SI de cada componente",
        ),
    ),
    PROJECTIVE_MEASUREMENT.identifier: (
        SettingField("tolerance", "tolerância das checagens de norma, hermiticidade e base"),
    ),
    WELL_DISCRETE_SPECTRUM.identifier: (_SUBINTERVALS, _LEVELS),
    OSCILLATOR_TRUNCATED_SPECTRUM.identifier: (
        _SUBINTERVALS,
        _LEVELS,
        SettingField("half_width", "meia largura do domínio, em comprimentos do oscilador"),
    ),
    WELL_TIME_EVOLUTION.identifier: (
        _SUBINTERVALS,
        SettingField("steps", "passos de tempo iguais"),
        SettingField("samples", "instantes salvos, com o inicial"),
    ),
}

DISPLAY_DIMENSIONS = {
    NumericalFamily.WELL_SPECTRUM: ENERGY,
    NumericalFamily.OSCILLATOR_SPECTRUM: ENERGY,
}

ARRAY_FIELDS = {
    InputSection.STATE: ArrayField(
        section="state",
        member="components",
        label="amplitudes do estado na base",
        rank=1,
        presence=Presence.REQUIRED,
        is_normalizable=True,
        has_unit=False,
    ),
    InputSection.OBSERVABLE: ArrayField(
        section="observable",
        member="matrix",
        label="matriz do observável na mesma base",
        rank=2,
        presence=Presence.REQUIRED,
        is_normalizable=False,
        has_unit=True,
    ),
    InputSection.BASIS: ArrayField(
        section="basis",
        member=None,
        label="vetores ortonormais de outra base, um por linha",
        rank=2,
        presence=Presence.REQUIRED,
        is_normalizable=False,
        has_unit=False,
    ),
    InputSection.INITIAL_STATE: ArrayField(
        section="initial_state",
        member="coefficients",
        label="coeficientes sobre os primeiros modos do poço",
        rank=1,
        presence=Presence.REQUIRED,
        is_normalizable=True,
        has_unit=False,
    ),
}
