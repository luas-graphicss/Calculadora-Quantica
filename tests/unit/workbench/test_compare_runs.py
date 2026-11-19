from pathlib import Path

import pytest

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.workbench.compare_runs import (
    ComparedValue,
    CompareRuns,
    InputDifference,
    VersionDivergence,
)
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.application.workbench.submit_run import Submission
from quantum_calculator.domain.execution import CalculationFailedError
from quantum_calculator.domain.workbench.documents import Document
from quantum_calculator.domain.workbench.runs import RunNotFoundError
from support.workbench import (
    INTERPRETATION,
    Bench,
    build_bench,
    closed_form_record,
    finish,
    raising,
)

_ONE_NANOMETRE = b'{"problem": "well", "parameters": {"width": {"value": 1, "unit": "nm"}}}'
_TWO_NANOMETRES = b'{"problem": "well", "parameters": {"width": {"value": 2, "unit": "nm"}}}'


@pytest.fixture
def bench(tmp_path: Path) -> Bench:
    return build_bench(tmp_path)


@pytest.fixture
def compare(bench: Bench) -> CompareRuns:
    return CompareRuns(
        ReadHistory(bench.runs, bench.artifacts), SiUnitRegistry(Codata2022Constants())
    )


def _wells(bench: Bench) -> tuple[str, str]:
    narrow = finish(
        bench, "key-1nm", _ONE_NANOMETRE, closed_form_record(_ONE_NANOMETRE, 3, 8, "0.375")
    )
    wide = finish(
        bench, "key-2nm", _TWO_NANOMETRES, closed_form_record(_TWO_NANOMETRES, 3, 32, "0.09375")
    )
    return narrow, wide


def test_doubling_the_width_shows_the_changed_input_and_a_quarter_of_the_energy(
    bench: Bench, compare: CompareRuns
) -> None:
    narrow, wide = _wells(bench)

    comparison = compare.execute(narrow, wide)

    assert comparison.input_differences == (InputDifference("/parameters/width/value", "1", "2"),)
    (energy,) = comparison.answers
    assert (energy.symbol, energy.label) == ("E", "energia do nível")
    assert energy.base == ComparedValue("0.375", "eV")
    assert energy.other == ComparedValue("0.09375", "eV")
    assert energy.ratio == "0.25"
    assert comparison.version_divergences == ()
    assert (comparison.base.identifier, comparison.other.identifier) == (narrow, wide)


def test_both_results_remain_in_the_history_after_the_comparison(
    bench: Bench, compare: CompareRuns
) -> None:
    narrow, wide = _wells(bench)

    compare.execute(narrow, wide)

    assert [run.headline for run in bench.runs.recent()] == ["E = 0.09375 eV", "E = 0.375 eV"]


def test_a_ratio_between_answers_in_different_units_is_taken_in_the_si(
    bench: Bench, compare: CompareRuns
) -> None:
    in_millielectronvolts = closed_form_record(_TWO_NANOMETRES, 375, 4, "93.75", unit="meV")
    narrow = finish(
        bench, "key-1nm", _ONE_NANOMETRE, closed_form_record(_ONE_NANOMETRE, 3, 8, "0.375")
    )
    wide = finish(bench, "key-2nm", _TWO_NANOMETRES, in_millielectronvolts)

    (energy,) = compare.execute(narrow, wide).answers

    assert energy.other == ComparedValue("93.75", "meV")
    assert energy.ratio == "0.25"


def test_version_divergences_name_what_differs_between_the_two_environments(
    bench: Bench, compare: CompareRuns
) -> None:
    upgraded = closed_form_record(_TWO_NANOMETRES, 3, 32, "0.09375")
    environment: Document = {
        "python": {"implementation": "CPython", "version": "3.12.9"},
        "platform": "Linux-test",
        "dependencies": [{"name": "numpy", "version": "2.6.0"}],
        "linear_algebra": [
            {"consumer": "numpy", "interface": "blas", "name": "openblas", "version": "0.4"}
        ],
    }
    upgraded = {**upgraded, "environment": environment, "constants": {"edition": "CODATA 2026"}}
    narrow = finish(
        bench, "key-1nm", _ONE_NANOMETRE, closed_form_record(_ONE_NANOMETRE, 3, 8, "0.375")
    )
    wide = finish(bench, "key-2nm", _TWO_NANOMETRES, upgraded)

    divergences = compare.execute(narrow, wide).version_divergences

    assert divergences == (
        VersionDivergence("constantes", "CODATA 2022", "CODATA 2026"),
        VersionDivergence("Python", "3.12.0", "3.12.9"),
        VersionDivergence("numpy", "2.5.5", "2.6.0"),
        VersionDivergence("blas usado por numpy", "openblas 0.3", "openblas 0.4"),
    )


def test_a_changed_method_is_reported(bench: Bench, compare: CompareRuns) -> None:
    narrow = finish(
        bench, "key-1nm", _ONE_NANOMETRE, closed_form_record(_ONE_NANOMETRE, 3, 8, "0.375")
    )
    bench.documents.interpretation = {
        **INTERPRETATION,
        "plan": {"method": "closed_form.infinite_square_well_energy"},
    }
    wide = finish(
        bench, "key-2nm", _TWO_NANOMETRES, closed_form_record(_TWO_NANOMETRES, 3, 32, "0.09375")
    )

    comparison = compare.execute(narrow, wide)

    assert comparison.base_method == "finite_difference.tridiagonal_eigensolver"
    assert comparison.other_method == "closed_form.infinite_square_well_energy"


def test_the_same_number_written_as_text_is_not_a_difference(
    bench: Bench, compare: CompareRuns
) -> None:
    as_text = _ONE_NANOMETRE.replace(b'"value": 1', b'"value": "1"')
    first = finish(
        bench, "key-1", _ONE_NANOMETRE, closed_form_record(_ONE_NANOMETRE, 3, 8, "0.375")
    )
    second = finish(bench, "key-2", as_text, closed_form_record(as_text, 3, 8, "0.375"))

    assert compare.execute(first, second).input_differences == ()


def test_added_removed_and_reordered_fields_are_located_by_pointer(
    bench: Bench, compare: CompareRuns
) -> None:
    before = b'{"conditions": ["y(0) = 1"], "numerics": {"levels": 3}, "notation": "text"}'
    after = b'{"conditions": ["y(0) = 2", "y(1) = 0"], "numerics": {}, "candidate": "y(t) = 0"}'
    first = finish(bench, "key-1", before, closed_form_record(before, 1, 1, "1"))
    second = finish(bench, "key-2", after, closed_form_record(after, 1, 1, "1"))

    assert compare.execute(first, second).input_differences == (
        InputDifference("/candidate", None, "y(t) = 0"),
        InputDifference("/conditions/0", "y(0) = 1", "y(0) = 2"),
        InputDifference("/conditions/1", None, "y(1) = 0"),
        InputDifference("/notation", "text", None),
        InputDifference("/numerics/levels", "3", None),
    )


def test_a_run_without_a_result_is_compared_by_its_input_only(
    bench: Bench, compare: CompareRuns
) -> None:
    narrow = finish(
        bench, "key-1nm", _ONE_NANOMETRE, closed_form_record(_ONE_NANOMETRE, 3, 8, "0.375")
    )
    bench.documents.calculation = raising(CalculationFailedError(-9))
    failed = bench.submit.execute(Submission(_TWO_NANOMETRES, "key-2nm", 30.0)).run.identifier
    bench.execute.execute(failed)

    comparison = compare.execute(narrow, failed)

    (energy,) = comparison.answers
    assert (energy.base, energy.other, energy.ratio) == (ComparedValue("0.375", "eV"), None, None)
    assert comparison.input_differences == (InputDifference("/parameters/width/value", "1", "2"),)
    assert comparison.version_divergences == ()


def test_comparing_with_a_run_that_is_not_in_the_history_is_refused(
    bench: Bench, compare: CompareRuns
) -> None:
    narrow, _ = _wells(bench)

    with pytest.raises(RunNotFoundError):
        compare.execute(narrow, "run-404")
