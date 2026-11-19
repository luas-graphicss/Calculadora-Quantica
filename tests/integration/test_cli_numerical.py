import itertools
import json
import math
from pathlib import Path
from typing import Any

import pytest

from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from support.cli import CliRunner
from support.numerical_documents import EXPECTATIONS, ExpectedAnswer, NumericalExpectation

EXIT_CODE_BY_VERIFICATION = {
    "passed": ExitCode.SUCCESS,
    "inconclusive": ExitCode.VERIFICATION_NOT_PASSED,
    "failed": ExitCode.VERIFICATION_NOT_PASSED,
}
ANALYTIC_GROUND_ENERGY = 0.3760301621
SECOND_ORDER = (1.8, 2.2)
WELL = "electron_box_1nm_discrete.json"
OSCILLATOR = "harmonic_oscillator_1ev.json"
BEAT = "electron_box_1nm_beat.json"


def _record(run_cli: CliRunner, case: Path) -> Any:
    return json.loads(run_cli("solve", case, "--format", "json").stdout)


def _answers(record: Any) -> dict[str, Any]:
    return {answer["name"]: answer for answer in record["result"]["answers"]}


def _column(record: Any, table: str, column: str) -> list[float]:
    tables = {item["name"]: item for item in record["result"]["tables"]}
    columns: dict[str, list[float]] = {
        item["name"]: item["values"] for item in tables[table]["columns"]
    }
    return columns[column]


def _statuses(record: Any) -> dict[str, str]:
    checks = record["verification"]["checks"]
    return {check["identifier"]: check["status"] for check in checks}


def _within(expected: ExpectedAnswer) -> object:
    return pytest.approx(
        expected["expected"],
        abs=expected.get("absolute_tolerance", 0.0),
        rel=expected.get("relative_tolerance", 0.0),
    )


def _observed_orders(errors: list[float]) -> list[float]:
    return [math.log2(coarse / fine) for coarse, fine in itertools.pairwise(errors)]


def test_every_numerical_reference_case_has_an_independent_oracle(numerical_cases: Path) -> None:
    cases = {path.name for path in numerical_cases.glob("*.json")} - {"expectations.json"}

    assert {case["file"] for case in EXPECTATIONS} == cases
    assert all(case["oracle"] for case in EXPECTATIONS)


@pytest.mark.numerical
@pytest.mark.parametrize("case", EXPECTATIONS, ids=lambda case: case["file"])
def test_solve_agrees_with_the_independent_oracle_within_the_declared_tolerance(
    run_cli: CliRunner, numerical_cases: Path, case: NumericalExpectation
) -> None:
    result = run_cli("solve", numerical_cases / case["file"], "--format", "json")

    record = json.loads(result.stdout)
    answers = _answers(record)
    assert result.stderr == ""
    assert result.exit_code == EXIT_CODE_BY_VERIFICATION[case["verification"]]
    assert record["document"] == "numerical_run_record"
    assert record["problem"]["card"]["identifier"] == case["card"]
    assert record["verification"]["status"] == case["verification"]
    assert [
        identifier for identifier, status in _statuses(record).items() if status != "passed"
    ] == case["not_passed"]
    assert record["result"]["nature"] == "approximate"
    for expected in case["answers"]:
        assert answers[expected["name"]]["value"] == _within(expected)


@pytest.mark.numerical
def test_decay_trajectory_follows_the_exponential_at_every_sampled_instant(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    record = _record(run_cli, numerical_cases / "decay_trajectory.json")

    instants = _column(record, "trajectory", "t")
    values = _column(record, "trajectory", "y")
    assert instants == pytest.approx([index / 10 for index in range(51)], abs=1e-12)
    assert (
        max(
            abs(value - math.exp(-instant)) for instant, value in zip(instants, values, strict=True)
        )
        <= 1e-8
    )


@pytest.mark.numerical
def test_well_levels_converge_at_second_order_towards_the_analytic_energies(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    record = _record(run_cli, numerical_cases / WELL)

    levels = _column(record, "refinement", "level")
    meshes = _column(record, "refinement", "subintervals")
    energies = _column(record, "refinement", "energy")
    assert sorted(set(meshes)) == [128, 256, 512]
    for level in (1, 2, 3):
        errors = [
            abs(energy - level**2 * ANALYTIC_GROUND_ENERGY)
            for row, mesh, energy in sorted(zip(levels, meshes, energies, strict=True))
            if row == level
        ]
        assert all(
            SECOND_ORDER[0] <= order <= SECOND_ORDER[1] for order in _observed_orders(errors)
        )


@pytest.mark.numerical
def test_discrete_and_analytic_ground_energies_agree_within_the_estimated_mesh_error(
    run_cli: CliRunner, numerical_cases: Path, reference_cases: Path
) -> None:
    analytic = json.loads(
        run_cli("solve", reference_cases / "electron_box_1nm.json", "--format", "json").stdout
    )
    discrete = _answers(_record(run_cli, numerical_cases / WELL))["energy_1"]

    exact = float(analytic["result"]["value"]["decimal"])
    estimate = discrete["estimate"]["value"]
    assert discrete["unit"] == analytic["result"]["value"]["unit"] == "eV"
    assert 0 < estimate < 1e-5
    assert abs(discrete["value"] - exact) <= 2 * estimate


@pytest.mark.numerical
def test_oscillator_domain_cut_is_measured_apart_from_the_mesh_error(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    record = _record(run_cli, numerical_cases / OSCILLATOR)

    half_widths = _column(record, "truncation", "half_width")
    energies = _column(record, "truncation", "energy")
    mesh_errors = [answer["estimate"]["value"] for answer in _answers(record).values()]
    changes = [
        abs(wide - narrow) / narrow
        for narrow, wide in zip(energies[0::2], energies[1::2], strict=True)
    ]
    assert len(set(half_widths)) == 2
    assert max(changes) <= 1e-9
    assert min(mesh_errors) > 1e3 * max(changes)
    assert {"mesh_refinement", "domain_truncation", "discrete_residual"} <= _statuses(record).keys()


@pytest.mark.numerical
def test_beat_phase_error_falls_at_second_order_in_the_time_step(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    record = _record(run_cli, numerical_cases / BEAT)

    steps = _column(record, "time_refinement", "steps")
    errors = _column(record, "time_refinement", "phase_error")
    assert steps == [256, 512, 1024]
    assert all(SECOND_ORDER[0] <= order <= SECOND_ORDER[1] for order in _observed_orders(errors))


def test_evolution_keeps_only_the_saved_observables_and_the_final_density(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    record = _record(run_cli, numerical_cases / BEAT)

    tables = {table["name"]: table["rows"] for table in record["result"]["tables"]}
    assert tables == {"observables": 9, "time_refinement": 3, "final_density": 257}
    assert max(_column(record, "observables", "norm")) == pytest.approx(1.0, abs=1e-9)


def test_under_resolved_mesh_is_not_reported_as_converged(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    result = run_cli("solve", numerical_cases / "electron_box_1nm_coarse.json")

    assert result.exit_code == ExitCode.VERIFICATION_NOT_PASSED
    assert result.stdout.splitlines()[3].endswith("verificação: inconclusive")
    assert "inconclusive [numerical_evidence] mesh_refinement" in result.stdout
    assert "não é declarada convergida" in result.stdout
    assert "passed [numerical_evidence] discrete_residual" in result.stdout


def test_narrow_domain_fails_on_the_domain_cut_while_the_mesh_study_passes(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    record = _record(run_cli, numerical_cases / "harmonic_oscillator_narrow.json")

    statuses = _statuses(record)
    assert statuses["mesh_refinement"] == "passed"
    assert statuses["discrete_residual"] == "passed"
    assert statuses["domain_truncation"] == "failed"


def test_first_lines_answer_with_each_level_its_unit_and_its_mesh_error(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    result = run_cli("solve", numerical_cases / WELL)

    first, second, third, summary, *_ = result.stdout.splitlines()
    assert result.exit_code == ExitCode.SUCCESS
    assert first.startswith("E_1 = 0.3760289823 eV; erro estimado 0.0000012 eV (erro de malha")
    assert second.startswith("E_2 = 1.504101772 eV; ")
    assert third.startswith("E_3 = 3.384175898 eV; ")
    assert summary == (
        "resultado approximate; 10 algarismos significativos, arredondamento half_even; "
        "verificação: passed"
    )


def test_measurement_answers_with_the_probability_of_each_outcome(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    result = run_cli("solve", numerical_cases / "spin_half_measurement.json")

    lower, upper, mean, *_ = result.stdout.splitlines()
    assert (lower, upper) == ("P(a = -1) = 0.500000000000", "P(a = 1) = 0.500000000000")
    assert mean.startswith("<A> = ")
    assert "normalização do estado (normalization): aplicada a pedido" in result.stdout


def test_validate_shows_the_reading_the_resolution_and_the_estimate_without_calculating(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    result = run_cli("validate", numerical_cases / WELL, "--time-limit", "5")

    assert result.exit_code == ExitCode.SUCCESS
    assert result.stderr == ""
    assert result.stdout.startswith(
        "Problema numérico válido: quantum.infinite_square_well.discrete_spectrum 1.0.0\n"
    )
    assert "limites: 5 s de relógio, 5 s de CPU e 2048 MiB de memória" in result.stdout
    assert "  largura do poço (width): 1E-9 m; entrada: 1 nm\n" in result.stdout
    assert "  subintervalos da malha uniforme (subintervals): 512\n" in result.stdout
    assert "\nEstimativa antes de alocar\n  memória: " in result.stdout
    assert "E_1 =" not in result.stdout


def test_validate_reads_the_integral_back_before_any_approximation(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    preview = json.loads(
        run_cli("validate", numerical_cases / "sine_quadrature.json", "--format", "json").stdout
    )

    inputs = {item["name"]: item for item in preview["problem"]["inputs"]}
    assert preview["document"] == "numerical_validation"
    assert preview["plan"]["nature"] == "approximate"
    assert inputs["statement"]["value"] == "integral(sin(x), x, 0, pi)"
    assert inputs["interval"]["value"] == f"de 0.0 a {math.pi!r}, adimensional"
    assert "result" not in preview


def test_long_table_is_previewed_in_text_and_complete_in_json(
    run_cli: CliRunner, numerical_cases: Path
) -> None:
    text = run_cli("solve", numerical_cases / WELL).stdout
    record = _record(run_cli, numerical_cases / WELL)

    assert "513 linhas; mostradas 17, igualmente espaçadas." in text
    assert len(_column(record, "eigenfunctions", "position")) == 513
    assert _column(record, "eigenfunctions", "psi_1")[0] == 0.0
    assert _column(record, "eigenfunctions", "psi_1")[-1] == 0.0


@pytest.mark.parametrize("output_format", ["text", "json"])
def test_the_same_numerical_problem_gives_byte_identical_output(
    run_cli: CliRunner, numerical_cases: Path, output_format: str
) -> None:
    arguments = ("solve", numerical_cases / BEAT, "--format", output_format)

    assert run_cli(*arguments).stdout == run_cli(*arguments).stdout
