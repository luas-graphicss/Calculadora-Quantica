from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.workbench.describe_catalog import DescribeCatalog
from quantum_calculator.domain.workbench.forms import (
    CardForm,
    ConstantChoice,
    CountField,
    InputKind,
    NotationFields,
    Presence,
    QuantityField,
    RequestedFields,
)

_ENERGY_UNITS = ("J", "eV", "meV", "keV", "MeV")
_LENGTH_UNITS = ("m", "mm", "μm", "nm", "Å", "pm")


def _form(card: str) -> CardForm:
    catalog = DescribeCatalog(
        SiUnitRegistry(Codata2022Constants()), Codata2022Constants()
    ).execute()
    forms = {
        choice.card.identifier: choice.form
        for question in catalog.questions
        for choice in question.choices
    }
    return forms[card]


def test_the_well_energy_form_asks_for_each_hypothesis_quantity_and_the_display_unit() -> None:
    form = _form("quantum.infinite_square_well.energy_level")

    assert form.kind is InputKind.PROBLEM
    assert [item.key for item in form.confirmations] == [
        "walls",
        "interior_potential",
        "boundary_wavefunction",
    ]
    assert form.quantities == (
        QuantityField(
            name="mass",
            symbol="m",
            label="massa da partícula",
            dimension="massa",
            units=("kg", "g", "mg"),
            constants=(ConstantChoice("electron_mass", "m_e", "massa do elétron"),),
        ),
        QuantityField(
            name="width",
            symbol="L",
            label="largura do poço",
            dimension="comprimento",
            units=_LENGTH_UNITS,
            constants=(),
        ),
    )
    assert form.counts == (CountField("level", "n", "índice do nível"),)
    assert form.requested == RequestedFields(
        "energy", "energia do nível", _ENERGY_UNITS, Presence.REQUIRED
    )
    assert form.covariance_models == ("independent",)
    assert (form.notation, form.arrays, form.settings) == (None, (), ())


def test_a_candidate_review_form_asks_for_the_equation_the_condition_and_the_candidate() -> None:
    form = _form("ode.first_order_linear.candidate_review")

    assert form.kind is InputKind.STATEMENT
    assert form.notation == NotationFields(
        has_statement=True,
        has_equations=False,
        has_conditions=True,
        has_candidate=True,
        symbols_carry_values=False,
    )
    assert form.requested is None


def test_a_derivative_form_has_no_condition_and_no_candidate() -> None:
    notation = _form("calculus.derivative").notation

    assert notation is not None
    assert (notation.has_conditions, notation.has_candidate) == (False, False)


def test_a_spectrum_form_asks_for_the_resolution_and_requires_an_energy_unit() -> None:
    form = _form("quantum.infinite_square_well.discrete_spectrum")

    assert form.kind is InputKind.NUMERICAL
    assert [setting.name for setting in form.settings] == ["subintervals", "levels"]
    assert form.requested == RequestedFields(
        None, "unidade de exibição das respostas", _ENERGY_UNITS, Presence.REQUIRED
    )
    assert form.notation is None


def test_a_trajectory_form_takes_equations_with_valued_symbols_and_no_display_unit() -> None:
    form = _form("ode.initial_value.explicit_runge_kutta")

    assert form.notation == NotationFields(
        has_statement=False,
        has_equations=True,
        has_conditions=True,
        has_candidate=False,
        symbols_carry_values=True,
    )
    assert form.requested == RequestedFields(
        None, "algarismos significativos das respostas", (), Presence.OPTIONAL
    )


def test_a_measurement_form_takes_the_state_the_observable_and_an_optional_basis() -> None:
    arrays = {
        array.section: array
        for array in _form("quantum.finite_basis.projective_measurement").arrays
    }

    assert list(arrays) == ["state", "observable", "basis"]
    assert (arrays["state"].rank, arrays["state"].member, arrays["state"].is_normalizable) == (
        1,
        "components",
        True,
    )
    assert (arrays["observable"].rank, arrays["observable"].has_unit) == (2, True)
    assert (arrays["basis"].presence, arrays["basis"].member) == (Presence.OPTIONAL, None)
    assert arrays["state"].presence is Presence.REQUIRED
