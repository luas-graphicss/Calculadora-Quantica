import os
import signal
from collections.abc import Iterator
from pathlib import Path

import pytest

from quantum_calculator.application.workbench.compare_runs import ComparedValue, InputDifference
from quantum_calculator.domain.workbench.runs import RunOrigin, RunState
from quantum_calculator.workbench_composition import Workbench, build_workbench
from support.processes import wait_until
from support.sessions import (
    LONG_CALCULATION,
    calculating,
    calculation_processes,
    settled,
    submit,
)

_WIDTH_OF_ONE_NANOMETRE = b'"value": 1,\n      "unit": "nm"'
_WIDTH_OF_TWO_NANOMETRES = b'"value": 2,\n      "unit": "nm"'


@pytest.fixture
def workbench(tmp_path: Path) -> Iterator[Workbench]:
    opened = build_workbench(tmp_path / "profile")
    yield opened
    opened.shut_down()


@pytest.fixture
def well(reference_cases: Path) -> bytes:
    return (reference_cases / "electron_box_1nm.json").read_bytes()


def test_widening_the_well_keeps_both_results_and_shows_a_quarter_of_the_energy(
    workbench: Workbench, well: bytes
) -> None:
    wider = well.replace(_WIDTH_OF_ONE_NANOMETRE, _WIDTH_OF_TWO_NANOMETRES)
    narrow = settled(workbench, submit(workbench, well, "session-key-1nm").identifier)

    wide = settled(
        workbench, submit(workbench, wider, "session-key-2nm", narrow.identifier).identifier
    )

    comparison = workbench.compare.execute(narrow.identifier, wide.identifier)
    (energy,) = comparison.answers
    assert wider != well
    assert (narrow.state, narrow.verification_status) == (RunState.SUCCEEDED, "passed")
    assert narrow.headline == "E = 0.3760301621 eV"
    assert wide.headline == "E = 0.09400754053 eV"
    assert wide.parent_identifier == narrow.identifier
    assert comparison.input_differences == (InputDifference("/parameters/width/value", "1", "2"),)
    assert energy.base == ComparedValue("0.3760301621", "eV")
    assert energy.other == ComparedValue("0.09400754053", "eV")
    assert energy.ratio == "0.25"
    assert comparison.version_divergences == ()
    assert [run.identifier for run in workbench.history.recent()] == [
        wide.identifier,
        narrow.identifier,
    ]


def test_a_package_is_imported_and_rerun_in_an_empty_profile_with_the_same_answer(
    workbench: Workbench, well: bytes, tmp_path: Path
) -> None:
    solved = settled(workbench, submit(workbench, well, "session-key-1nm").identifier)
    package = workbench.export_package.execute(solved.identifier).content
    elsewhere = build_workbench(tmp_path / "another-profile")
    try:
        imported = elsewhere.import_package.execute(package).run
        before_rerun = elsewhere.history.recent()
        details = elsewhere.history.details(imported.identifier)
        rerun = settled(
            elsewhere,
            submit(elsewhere, details.source, "session-key-rerun", imported.identifier).identifier,
        )
        comparison = elsewhere.compare.execute(imported.identifier, rerun.identifier)
    finally:
        elsewhere.shut_down()

    (energy,) = comparison.answers
    assert before_rerun == (imported,)
    assert (imported.origin, imported.state) == (RunOrigin.IMPORTED, RunState.SUCCEEDED)
    assert details.source == well
    assert (rerun.origin, rerun.state, rerun.verification_status) == (
        RunOrigin.LOCAL,
        RunState.SUCCEEDED,
        "passed",
    )
    assert rerun.headline == imported.headline == "E = 0.3760301621 eV"
    assert (energy.ratio, comparison.input_differences) == ("1", ())
    assert comparison.version_divergences == ()
    assert rerun.require_artifact("problem") == imported.require_artifact("problem")


def test_cancelling_a_long_calculation_releases_the_worker_for_the_next_run(
    workbench: Workbench, well: bytes
) -> None:
    long_run = submit(workbench, LONG_CALCULATION, "session-key-long")
    calculating(workbench, long_run.identifier)

    cancelled = workbench.cancel.execute(long_run.identifier)

    wait_until(lambda: not calculation_processes())
    following = settled(workbench, submit(workbench, well, "session-key-next").identifier)
    assert cancelled.state is RunState.CANCELLED
    assert workbench.history.run(long_run.identifier) == cancelled
    assert (cancelled.verification_status, cancelled.headline) == (None, None)
    assert workbench.history.details(long_run.identifier).outcome is None
    assert following.state is RunState.SUCCEEDED


def test_a_calculation_process_that_is_killed_fails_its_run_and_spares_the_others(
    workbench: Workbench, well: bytes
) -> None:
    earlier = settled(workbench, submit(workbench, well, "session-key-earlier").identifier)
    doomed = submit(workbench, LONG_CALCULATION, "session-key-doomed")

    os.kill(calculating(workbench, doomed.identifier), signal.SIGTERM)

    failed = settled(workbench, doomed.identifier)
    following = settled(workbench, submit(workbench, well, "session-key-next").identifier)
    assert (failed.state, failed.failure_category) == (RunState.FAILED, "calculation_failed")
    assert (failed.verification_status, failed.headline) == (None, None)
    assert workbench.history.run(earlier.identifier) == earlier
    assert workbench.history.complete_outcome(earlier.identifier) is not None
    assert following.state is RunState.SUCCEEDED


def test_repeating_a_submission_while_it_calculates_does_not_start_a_second_job(
    workbench: Workbench,
) -> None:
    first = submit(workbench, LONG_CALCULATION, "session-key-long")
    calculating(workbench, first.identifier)

    repeated = submit(workbench, LONG_CALCULATION, "session-key-long")
    workbench.cancel.execute(first.identifier)

    assert repeated.identifier == first.identifier
    assert len(workbench.history.recent()) == 1
    wait_until(lambda: not calculation_processes())


def test_stopping_the_workbench_interrupts_the_calculation_and_a_restart_shows_no_result(
    tmp_path: Path,
) -> None:
    first = build_workbench(tmp_path / "profile")
    unfinished = submit(first, LONG_CALCULATION, "session-key-long")
    calculating(first, unfinished.identifier)
    first.shut_down()

    restarted = build_workbench(tmp_path / "profile")
    try:
        report = restarted.recover.execute()
        seen = restarted.history.run(unfinished.identifier)
        outcome = restarted.history.details(unfinished.identifier).outcome
    finally:
        restarted.shut_down()

    assert report.interrupted_runs == 0
    assert seen.state is RunState.INTERRUPTED
    assert (seen.verification_status, seen.headline, outcome) == (None, None, None)
    wait_until(lambda: not calculation_processes())
