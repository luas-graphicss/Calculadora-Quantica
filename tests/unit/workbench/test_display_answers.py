import json
from pathlib import Path

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.workbench.display_answers import (
    AnswerDisplay,
    DisplayAnswers,
    DisplayUnitRefusedError,
)
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.domain.workbench.documents import Document
from support.workbench import RECORD, SOURCE, Bench, build_bench, finish

_ENERGY_UNITS = ("J", "eV", "meV", "keV", "MeV")


@pytest.fixture
def bench(tmp_path: Path) -> Bench:
    return build_bench(tmp_path)


@pytest.fixture
def display(bench: Bench) -> DisplayAnswers:
    return DisplayAnswers(
        ReadHistory(bench.runs, bench.artifacts), SiUnitRegistry(Codata2022Constants())
    )


def _recorded(repository_root: Path, evidence: str) -> Document:
    document: Document = json.loads((repository_root / "docs" / "evidence" / evidence).read_text())
    return document


def _shown(display: AnswerDisplay) -> list[tuple[str, str, str, str | None]]:
    return [(answer.symbol, answer.value, answer.unit, answer.error) for answer in display.answers]


def test_the_stored_answer_is_shown_as_it_was_reported(
    bench: Bench, display: DisplayAnswers, repository_root: Path
) -> None:
    record = _recorded(repository_root, "phase-1/electron_box_1nm.run_record.json")
    identifier = finish(bench, "submission-key-0001", SOURCE, record)

    shown = display.execute(identifier, None)

    assert shown.alternatives == _ENERGY_UNITS
    assert _shown(shown) == [("E", "0.3760301621", "eV", None)]
    assert shown.answers[0].label == "energia do nível"


def test_an_exact_answer_is_converted_from_its_rational_value_without_a_new_calculation(
    bench: Bench, display: DisplayAnswers, repository_root: Path
) -> None:
    record = _recorded(repository_root, "phase-1/electron_box_1nm.run_record.json")
    identifier = finish(bench, "submission-key-0001", SOURCE, record)
    calculations = len(bench.documents.calculated)

    in_joules = display.execute(identifier, "J")
    in_millielectronvolts = display.execute(identifier, "meV")

    assert _shown(in_joules) == [("E", "6.024667394E-20", "J", None)]
    assert _shown(in_millielectronvolts) == [("E", "376.0301621", "meV", None)]
    assert len(bench.documents.calculated) == calculations
    assert bench.runs.recent()[0].headline == "E = 0.3760301621 eV"


def test_a_propagated_uncertainty_follows_the_display_unit(
    bench: Bench, display: DisplayAnswers, repository_root: Path
) -> None:
    record = _recorded(repository_root, "phase-1/electron_box_1nm_uncertainty.run_record.json")
    identifier = finish(bench, "submission-key-0001", SOURCE, record)

    reported = display.execute(identifier, None).answers[0]
    converted = display.execute(identifier, "meV").answers[0]

    assert (reported.error, converted.error) == ("0.0075", "7.5")
    assert converted.error_origin == (
        "incerteza-padrão por propagação linear, covariância independent"
    )


def test_numerical_answers_and_their_error_estimates_are_converted_together(
    bench: Bench, display: DisplayAnswers, repository_root: Path
) -> None:
    record = _recorded(repository_root, "phase-3/electron_box_1nm_discrete.run_record.json")
    identifier = finish(bench, "submission-key-0001", SOURCE, record)

    shown = display.execute(identifier, "meV")

    assert _shown(shown) == [
        ("E_1", "376.0289823", "meV", "0.0012"),
        ("E_2", "1504.101772", "meV", "0.019"),
        ("E_3", "3384.175898", "meV", "0.096"),
    ]


@pytest.mark.parametrize("unit", ["nm", "furlong", ""])
def test_a_unit_of_another_dimension_or_unknown_is_refused(
    bench: Bench, display: DisplayAnswers, unit: str
) -> None:
    identifier = finish(bench, "submission-key-0001", SOURCE, RECORD)

    with pytest.raises(DisplayUnitRefusedError) as refused:
        display.execute(identifier, unit)

    assert refused.value.alternatives == _ENERGY_UNITS


def test_a_symbolic_answer_offers_no_unit_conversion(
    bench: Bench, display: DisplayAnswers, repository_root: Path
) -> None:
    record = _recorded(repository_root, "phase-2/decay_initial_value.run_record.json")
    identifier = finish(bench, "submission-key-0001", SOURCE, record)

    assert display.execute(identifier, None) == AnswerDisplay(alternatives=(), answers=())
