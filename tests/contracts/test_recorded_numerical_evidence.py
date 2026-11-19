import json
from pathlib import Path

import pytest

from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from support.cli import CliRunner
from support.evidence import declared_content, measured_series, report_outline, unit_scales

RECORDED_RUN_RECORDS = [
    "sine_quadrature",
    "decay_trajectory",
    "spin_half_measurement",
    "electron_box_1nm_discrete",
    "electron_box_1nm_coarse",
    "harmonic_oscillator_1ev",
    "electron_box_1nm_beat",
]
RECORDED_REPORTS = [
    *RECORDED_RUN_RECORDS,
    "spin_half_measurement_rotated",
    "degenerate_measurement",
    "harmonic_oscillator_narrow",
]
RECORDED_PREVIEWS = ["electron_box_1nm_discrete", "sine_quadrature"]
RECORDED_REFUSALS = {
    "non_hermitian_operator": ExitCode.INVALID_INPUT,
    "zero_state": ExitCode.INVALID_INPUT,
    "incompatible_condition": ExitCode.INVALID_INPUT,
    "missing_initial_state": ExitCode.INVALID_INPUT,
    "resource_limit": ExitCode.BUDGET_EXCEEDED,
    "estimated_work_too_large": ExitCode.BUDGET_EXCEEDED,
    "divergent_integral": ExitCode.NON_CONVERGENT,
    "blow_up_trajectory": ExitCode.NON_CONVERGENT,
}
RELATIVE_TOLERANCE = 1e-6
ABSOLUTE_TOLERANCE_PER_UNIT_SCALE = 1e-9


@pytest.fixture(scope="module")
def evidence(repository_root: Path) -> Path:
    return repository_root / "docs" / "evidence" / "phase-3"


@pytest.mark.numerical
@pytest.mark.parametrize("case", RECORDED_RUN_RECORDS)
def test_recorded_numerical_record_is_reproduced_within_floating_point_tolerance(
    run_cli: CliRunner, numerical_cases: Path, evidence: Path, case: str
) -> None:
    recorded = json.loads((evidence / f"{case}.run_record.json").read_text("utf-8"))

    result = run_cli("solve", numerical_cases / f"{case}.json", "--format", "json")

    reproduced = json.loads(result.stdout)
    assert declared_content(reproduced) == declared_content(recorded)
    expected = measured_series(recorded)
    scales = unit_scales(expected)
    for current, reference in zip(measured_series(reproduced), expected, strict=True):
        assert current.values == pytest.approx(
            reference.values,
            rel=RELATIVE_TOLERANCE,
            abs=ABSOLUTE_TOLERANCE_PER_UNIT_SCALE * scales[reference.unit],
        ), reference.name


@pytest.mark.parametrize("case", RECORDED_REPORTS)
def test_recorded_numerical_report_keeps_its_answers_sections_and_verdict(
    run_cli: CliRunner, numerical_cases: Path, evidence: Path, case: str
) -> None:
    recorded = (evidence / f"{case}.solve.txt").read_text("utf-8")

    result = run_cli("solve", numerical_cases / f"{case}.json")

    assert report_outline(result.stdout) == report_outline(recorded)


@pytest.mark.parametrize("case", RECORDED_PREVIEWS)
def test_recorded_numerical_preview_is_what_the_cli_produces_now(
    run_cli: CliRunner, numerical_cases: Path, evidence: Path, case: str
) -> None:
    recorded = (evidence / f"{case}.validate.txt").read_text("utf-8")

    assert run_cli("validate", numerical_cases / f"{case}.json").stdout == recorded


@pytest.mark.parametrize("case", RECORDED_REFUSALS)
def test_recorded_numerical_refusal_is_what_the_cli_produces_now(
    run_cli: CliRunner, numerical_cases: Path, evidence: Path, case: str
) -> None:
    recorded = (evidence / f"{case}.rejection.txt").read_text("utf-8")

    result = run_cli("solve", numerical_cases / "rejected" / f"{case}.json")

    assert result.exit_code == RECORDED_REFUSALS[case]
    assert result.stdout == ""
    assert result.stderr == recorded


def test_recorded_json_refusal_is_what_the_cli_produces_now(
    run_cli: CliRunner, numerical_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "non_hermitian_operator.rejection.json").read_text("utf-8")

    result = run_cli(
        "solve",
        numerical_cases / "rejected" / "non_hermitian_operator.json",
        "--format",
        "json",
    )

    assert result.exit_code == ExitCode.INVALID_INPUT
    assert result.stderr == recorded


def test_recorded_numerical_budget_refusal_is_what_the_cli_produces_now(
    run_cli: CliRunner, numerical_cases: Path, evidence: Path
) -> None:
    recorded = (evidence / "time_budget_exceeded.rejection.txt").read_text("utf-8")

    result = run_cli(
        "solve", numerical_cases / "electron_box_1nm_discrete.json", "--time-limit", "0.05"
    )

    assert result.exit_code == ExitCode.BUDGET_EXCEEDED
    assert result.stdout == ""
    assert result.stderr == recorded
