import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from support.processes import has_child_running, session_is_empty, wait_until


def _run(arguments: list[str], working_directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "quantum_calculator", *arguments],
        capture_output=True,
        check=False,
        cwd=working_directory,
        encoding="utf-8",
        timeout=120,
    )


def test_reference_case_is_reproduced_from_another_working_directory(
    reference_cases: Path, tmp_path: Path
) -> None:
    case = str(reference_cases / "electron_box_1nm.json")

    validated = _run(["validate", case], tmp_path)
    solved = _run(["solve", case, "--format", "json"], tmp_path)

    assert validated.returncode == 0
    assert solved.returncode == 0
    assert solved.stderr == ""
    assert json.loads(solved.stdout)["result"]["value"]["decimal"] == "0.3760301621"


def test_rejected_input_sets_the_process_exit_code(reference_cases: Path, tmp_path: Path) -> None:
    case = str(reference_cases / "rejected" / "width_in_seconds.json")

    completed = _run(["solve", case, "--format", "json"], tmp_path)

    assert completed.returncode == 3
    assert completed.stdout == ""
    assert json.loads(completed.stderr)["category"] == "invalid_input"


def test_statement_is_solved_from_another_working_directory(
    symbolic_cases: Path, tmp_path: Path
) -> None:
    case = str(symbolic_cases / "parabola_area.json")

    solved = _run(["solve", case, "--format", "json"], tmp_path)

    assert solved.returncode == 0
    assert solved.stderr == ""
    assert json.loads(solved.stdout)["result"]["answer"]["text"] == "integral(x^2, x, 0, 1) = 1/3"


def test_numerical_problem_is_solved_from_another_working_directory(
    numerical_cases: Path, tmp_path: Path
) -> None:
    case = str(numerical_cases / "electron_box_1nm_discrete.json")

    solved = _run(["solve", case, "--format", "json"], tmp_path)

    ground, *_ = json.loads(solved.stdout)["result"]["answers"]
    assert solved.returncode == 0
    assert solved.stderr == ""
    assert (ground["name"], ground["display"], ground["unit"]) == ("energy_1", "0.3760289823", "eV")


def test_method_that_does_not_converge_sets_its_own_exit_code(
    numerical_cases: Path, tmp_path: Path
) -> None:
    case = str(numerical_cases / "rejected" / "blow_up_trajectory.json")

    completed = _run(["solve", case, "--format", "json"], tmp_path)

    assert completed.returncode == 9
    assert completed.stdout == ""
    assert json.loads(completed.stderr)["category"] == "non_convergent"


@pytest.mark.parametrize(
    "case", ["symbolic/product_rule.json", "numerical/electron_box_1nm_beat.json"]
)
def test_interrupt_cancels_the_calculation_and_leaves_no_process_behind(
    repository_root: Path, tmp_path: Path, case: str
) -> None:
    case = str(repository_root / "reference_cases" / case)
    with subprocess.Popen(
        [sys.executable, "-m", "quantum_calculator", "solve", case],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
        encoding="utf-8",
        start_new_session=True,
    ) as process:
        wait_until(lambda: has_child_running(process.pid, b"multiprocessing"))
        os.killpg(process.pid, signal.SIGINT)
        stdout, stderr = process.communicate(timeout=60)

    assert process.returncode == 130
    assert stdout == ""
    assert stderr == "qcalc: cálculo cancelado; nenhum resultado parcial foi aproveitado.\n"
    wait_until(lambda: session_is_empty(process.pid))
