import json
import subprocess
import sys
from pathlib import Path


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
