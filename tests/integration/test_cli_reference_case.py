import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from support.cli import CliRunner, write_document
from support.documents import ProblemDocument

ANGSTROM = "\N{LATIN CAPITAL LETTER A WITH RING ABOVE}"
REFERENCE_ENERGY_IN_EV = (
    Fraction("6.62607015e-34") ** 2
    / (8 * Fraction("9.1093837139e-31") * Fraction(1, 10**18))
    / Fraction("1.602176634e-19")
)


def _exact(encoded: dict[str, str]) -> Fraction:
    return Fraction(int(encoded["numerator"]), int(encoded["denominator"]))


def test_validate_shows_the_interpretation_without_computing(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    result = run_cli("validate", reference_cases / "electron_box_1nm.json")

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout.startswith(
        "Entrada válida: quantum.infinite_square_well.energy_level 1.0.0\n"
    )
    assert "L = 1E-9 m; entrada: 1 nm" in result.stdout
    assert "m = 9.1093837139E-31 kg; constante electron_mass do catálogo" in result.stdout
    assert "0.37603" not in result.stdout


@pytest.mark.numerical
def test_solve_reproduces_the_reference_energy_within_the_oracle_tolerance(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    oracle = json.loads((reference_cases / "electron_box_1nm.expected.json").read_text("utf-8"))

    result = run_cli("solve", reference_cases / oracle["case"], "--format", "json")

    value = json.loads(result.stdout)["result"]["value"]
    assert result.exit_code == 0
    assert result.stderr == ""
    assert value["unit"] == oracle["unit"]
    assert abs(Decimal(value["decimal"]) - Decimal(oracle["nominal_value"])) <= Decimal(
        oracle["absolute_tolerance"]
    )


@pytest.mark.algebraic
def test_solve_carries_the_exact_fraction_behind_the_rounded_decimal(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    result = run_cli("solve", reference_cases / "electron_box_1nm.json", "--format", "json")

    value = json.loads(result.stdout)["result"]["value"]
    assert _exact(value) == REFERENCE_ENERGY_IN_EV
    assert value["is_exact"] is False


def test_solve_states_expression_unit_constants_hypotheses_and_input(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    case = reference_cases / "electron_box_1nm.json"

    record = json.loads(run_cli("solve", case, "--format", "json").stdout)

    constants = {constant["identifier"]: constant for constant in record["constants"]["used"]}
    assert record["document"] == "run_record"
    assert record["result"]["expression"]["plain"] == "E_n = h**2*n**2/(8*L**2*m)"
    assert record["result"]["nature"] == "exact"
    assert record["plan"]["rounding"] == {"mode": "half_even", "significant_digits": 10}
    assert record["constants"]["edition"] == "CODATA 2022"
    assert list(constants) == ["planck_constant", "electron_mass", "electron_volt"]
    assert constants["planck_constant"]["value"]["decimal"] == "6.62607015E-34"
    assert constants["electron_mass"]["exactness"] == "measured"
    assert constants["electron_mass"]["standard_uncertainty"]["decimal"] == "2.8E-40"
    assert {item["key"]: item["value"] for item in record["problem"]["hypotheses"]} == {
        "walls": "infinite",
        "interior_potential": "zero",
        "boundary_wavefunction": "zero",
    }
    assert record["verification"]["status"] == "passed"
    assert record["input"]["text"] == case.read_text("utf-8")
    assert record["input"]["sha256"] == hashlib.sha256(case.read_bytes()).hexdigest()
    assert record["environment"]["package"]["name"] == "quantum-calculator"


def test_no_error_bar_is_shown_when_no_uncertainty_was_declared(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    case = reference_cases / "electron_box_1nm.json"

    record = json.loads(run_cli("solve", case, "--format", "json").stdout)
    text = run_cli("solve", case).stdout

    assert record["result"]["uncertainty"]["status"] == "not_evaluated"
    assert "não avaliada" in text
    assert "u(E)" not in text


def test_text_report_answers_the_question_on_the_first_line(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    result = run_cli("solve", reference_cases / "electron_box_1nm.json")

    first_line, second_line, *_ = result.stdout.splitlines()
    assert result.exit_code == 0
    assert first_line == "E = 0.3760301621 eV"
    assert "verificação: passed" in second_line


@pytest.mark.parametrize("output_format", ["text", "json"])
def test_the_same_input_gives_byte_identical_output(
    run_cli: CliRunner, reference_cases: Path, output_format: str
) -> None:
    arguments = ("solve", reference_cases / "electron_box_1nm.json", "--format", output_format)

    assert run_cli(*arguments).stdout == run_cli(*arguments).stdout


@pytest.mark.numerical
def test_declared_independent_uncertainties_reach_the_output(
    run_cli: CliRunner, reference_cases: Path
) -> None:
    oracle = json.loads(
        (reference_cases / "electron_box_1nm_uncertainty.expected.json").read_text("utf-8")
    )
    case = reference_cases / oracle["case"]

    uncertainty = json.loads(run_cli("solve", case, "--format", "json").stdout)["result"][
        "uncertainty"
    ]
    text = run_cli("solve", case).stdout

    assert uncertainty["status"] == "evaluated"
    assert uncertainty["covariance"] == oracle["covariance"]
    assert uncertainty["standard_uncertainty"] == {
        "decimal": oracle["standard_uncertainty"],
        "unit": oracle["unit"],
    }
    assert uncertainty["relative_standard_uncertainty"] == oracle["relative_standard_uncertainty"]
    assert [item["parameter"] for item in uncertainty["contributions"]] == ["mass", "width"]
    assert f"u(E) = {oracle['standard_uncertainty']} eV; relativa 0.020" in text


@pytest.mark.algebraic
def test_width_in_angstrom_gives_the_same_exact_result(
    run_cli: CliRunner, reference_cases: Path, electron_box: ProblemDocument, tmp_path: Path
) -> None:
    in_angstrom = electron_box.with_value("/parameters/width", {"value": 10, "unit": ANGSTROM})
    variant = write_document(tmp_path, in_angstrom.encode())

    reference = json.loads(
        run_cli("solve", reference_cases / "electron_box_1nm.json", "--format", "json").stdout
    )
    converted = json.loads(run_cli("solve", variant, "--format", "json").stdout)

    assert converted["result"]["value"] == reference["result"]["value"]
    assert converted["result"]["si_value"] == reference["result"]["si_value"]


def test_extreme_magnitudes_within_the_literal_limits_are_solved_and_verified(
    run_cli: CliRunner, uncertain_electron_box: ProblemDocument, tmp_path: Path
) -> None:
    extreme = (
        uncertain_electron_box.with_value("/parameters/mass", {"value": "9e-99", "unit": "mg"})
        .with_value("/parameters/width", {"value": "1e-99", "unit": "pm"})
        .with_value("/parameters/level", "1e99")
        .with_value("/uncertainty/standard_uncertainties/mass", {"value": "9e-99", "unit": "mg"})
        .with_value("/uncertainty/standard_uncertainties/width", {"value": "1e-99", "unit": "pm"})
    )

    result = run_cli("solve", write_document(tmp_path, extreme.encode()), "--format", "json")

    record = json.loads(result.stdout)
    assert result.exit_code == 0
    assert record["verification"]["status"] == "passed"
    assert record["result"]["uncertainty"]["relative_standard_uncertainty"] == "2.2"
