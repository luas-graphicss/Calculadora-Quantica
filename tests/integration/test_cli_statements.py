import json
from pathlib import Path
from typing import TypedDict

import pytest

from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from quantum_calculator.interfaces.serialization.decoding.statement_decoder import decode_statement
from support.cli import CliRunner, write_document
from support.statements import CALCULUS, KINEMATICS, statement_document
from support.symbolic import answer_value, same_function


class SymbolicExpectation(TypedDict):
    file: str
    card: str
    answer: str
    derivation: str
    verification: str
    failed_checks: list[str]
    validity: list[str]
    arbitrary_constants: list[str]


SYMBOLIC = Path(__file__).resolve().parents[2] / "reference_cases" / "symbolic"
EXPECTATIONS: list[SymbolicExpectation] = json.loads(
    (SYMBOLIC / "expectations.json").read_text("utf-8")
)["cases"]
EXIT_CODE_BY_VERIFICATION = {
    "passed": ExitCode.SUCCESS,
    "failed": ExitCode.VERIFICATION_NOT_PASSED,
}
PRODUCT_IN_LATEX = "\\frac{d}{dx}\\left(x^{2} \\sin(x)\\right)"
PRODUCT_TREE = "(derivative ordinary x 1 (multiply (power (symbol x) (number 2)) (sin (symbol x))))"


def test_every_symbolic_reference_case_has_a_hand_derived_expectation(
    symbolic_cases: Path,
) -> None:
    cases = {path.name for path in symbolic_cases.glob("*.json")} - {"expectations.json"}

    assert {case["file"] for case in EXPECTATIONS} == cases
    assert all(case["derivation"] for case in EXPECTATIONS)


def test_validate_previews_the_reading_as_text_latex_and_tree_without_solving(
    run_cli: CliRunner, symbolic_cases: Path
) -> None:
    result = run_cli("validate", symbolic_cases / "product_rule.json")

    assert result.exit_code == ExitCode.SUCCESS
    assert result.stderr == ""
    assert result.stdout.startswith("Enunciado válido: calculus.derivative 1.0.0\n")
    assert "  texto: diff(x^2*sin(x), x)\n" in result.stdout
    assert (
        "  LaTeX: \\frac{d}{dx}\\left(x^{2} \\cdot \\sin\\left(x\\right)\\right)\n" in result.stdout
    )
    assert f"  árvore: {PRODUCT_TREE}\n" in result.stdout
    assert "cos(x)" not in result.stdout


def test_text_and_latex_statements_are_previewed_as_the_same_problem(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    in_text = statement_document("diff(x^2 sin(x), x)", CALCULUS)
    in_latex = statement_document(PRODUCT_IN_LATEX, CALCULUS, "latex")

    from_text = json.loads(
        run_cli("validate", write_document(tmp_path, in_text), "--format", "json").stdout
    )
    from_latex = json.loads(
        run_cli("validate", write_document(tmp_path, in_latex), "--format", "json").stdout
    )

    assert from_text["problem"]["statement"]["structure"] == PRODUCT_TREE
    assert from_latex["problem"]["statement"]["structure"] == PRODUCT_TREE
    assert from_latex["problem"]["statement"]["source"] == PRODUCT_IN_LATEX
    assert from_text["problem"]["card"] == from_latex["problem"]["card"]


def test_only_compatible_card_is_suggested_and_the_preview_asks_for_confirmation(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    document = statement_document("diff(x^2, x)", CALCULUS)

    text = run_cli("validate", write_document(tmp_path, document)).stdout
    preview = json.loads(
        run_cli("validate", write_document(tmp_path, document), "--format", "json").stdout
    )

    assert "calculus.derivative 1.0.0 (sugerida por ser a única compatível)" in text
    assert 'para confirmar, declare "problem": "calculus.derivative" na entrada' in text
    assert preview["problem"]["card"]["selection"] == "suggested"


def test_validate_shows_the_budget_the_calculation_would_run_under(
    run_cli: CliRunner, symbolic_cases: Path
) -> None:
    case = symbolic_cases / "product_rule.json"

    text = run_cli("validate", case, "--time-limit", "5").stdout
    preview = json.loads(run_cli("validate", case, "--time-limit", "5", "--format", "json").stdout)

    assert "limites: 5 s de relógio, 5 s de CPU e 2048 MiB de memória" in text
    assert preview["plan"]["budget"] == {
        "wall_seconds": 5.0,
        "cpu_seconds": 5,
        "memory_bytes": 2048 * 1024**2,
    }


@pytest.mark.parametrize("case", EXPECTATIONS, ids=lambda case: case["file"])
def test_solve_reproduces_the_hand_derived_answer_and_verdict(
    run_cli: CliRunner,
    symbolic_cases: Path,
    statement_validator: StatementValidator,
    case: SymbolicExpectation,
) -> None:
    path = symbolic_cases / case["file"]
    problem = statement_validator.validate(decode_statement(path.read_bytes()))

    result = run_cli("solve", path, "--format", "json")

    record = json.loads(result.stdout)
    solved = record["result"]
    constants = tuple(solved["arbitrary_constants"])
    checks = record["verification"]["checks"]
    assert result.stderr == ""
    assert result.exit_code == EXIT_CODE_BY_VERIFICATION[case["verification"]]
    assert record["problem"]["card"]["identifier"] == case["card"]
    assert record["verification"]["status"] == case["verification"]
    assert [check["identifier"] for check in checks if check["status"] == "failed"] == case[
        "failed_checks"
    ]
    assert list(constants) == case["arbitrary_constants"]
    assert [condition["text"] for condition in solved["validity"]] == case["validity"]
    assert same_function(
        problem,
        constants,
        answer_value(problem, constants, solved["answer"]["text"]),
        case["answer"],
    )
    assert not [
        check
        for check in checks
        if check["kind"] == "numerical_evidence" and check["status"] == "passed"
    ]


def test_solve_answers_on_the_first_line_and_states_domain_and_constant(
    run_cli: CliRunner, symbolic_cases: Path
) -> None:
    result = run_cli("solve", symbolic_cases / "reciprocal_primitive.json")

    first_line, second_line, *_ = result.stdout.splitlines()
    assert result.exit_code == ExitCode.SUCCESS
    assert first_line == "integral(1/x, x) = ln(abs(x)) + C"
    assert second_line == "resultado exact; adimensional; verificação: passed"
    assert "\nValidade\n  vale onde x \N{NOT EQUAL TO} 0\n" in result.stdout
    assert "\nConstantes arbitrárias\n  C\n" in result.stdout


def test_result_states_the_coherent_unit_of_the_declared_quantities(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    document = statement_document("integral(g*t, t, 0, tau)", KINEMATICS)

    text = run_cli("solve", write_document(tmp_path, document)).stdout
    record = json.loads(
        run_cli("solve", write_document(tmp_path, document), "--format", "json").stdout
    )

    assert text.splitlines()[1] == "resultado exact; unidade coerente do SI: m; verificação: passed"
    assert record["result"]["unit"] == "m"
    assert record["problem"]["result_unit"] == "m"


def test_unconfirmed_parameter_sign_makes_the_answer_conditional_with_its_special_case(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    rates = {
        "t": {"role": "variable", "domain": "real", "unit": "s"},
        "a": {"role": "parameter", "domain": "real", "unit": "1/s"},
        "s": {"role": "parameter", "domain": "real", "unit": "1/s"},
        "y": {"role": "function", "domain": "real", "unit": "1", "argument": "t"},
    }

    result = run_cli("solve", write_document(tmp_path, statement_document("y' = a*y + s", rates)))

    assert result.exit_code == ExitCode.VERIFICATION_NOT_PASSED
    assert result.stdout.splitlines()[1].endswith("verificação: conditional")
    assert (
        "\nHipóteses que o domínio declarado não confirma\n  a \N{NOT EQUAL TO} 0\n"
        in result.stdout
    )
    assert "\nCasos especiais\n  se a = 0: y(t) = " in result.stdout


def test_review_reports_a_wrong_initial_value_and_a_wrong_sign_as_different_failures(
    run_cli: CliRunner, symbolic_cases: Path
) -> None:
    wrong_value = run_cli("solve", symbolic_cases / "decay_candidate_wrong_initial_value.json")
    wrong_sign = run_cli("solve", symbolic_cases / "decay_candidate_wrong_sign.json")

    assert wrong_value.exit_code == ExitCode.VERIFICATION_NOT_PASSED
    assert wrong_sign.exit_code == ExitCode.VERIFICATION_NOT_PASSED
    assert wrong_value.stdout.splitlines()[:2] == [
        "Candidata reprovada: y(t) = 2*y_0*exp(-k*t)",
        "revisão por substituição; adimensional; verificação: failed (initial_condition)",
    ]
    assert wrong_sign.stdout.splitlines()[:2] == [
        "Candidata reprovada: y(t) = y_0*exp(k*t)",
        "revisão por substituição; adimensional; verificação: failed (equation_residual)",
    ]
    assert "passed [proof] equation_residual" in wrong_value.stdout
    assert "failed [proof] initial_condition" in wrong_value.stdout
    assert "failed [proof] equation_residual" in wrong_sign.stdout
    assert "passed [proof] initial_condition" in wrong_sign.stdout


def test_correct_candidate_is_approved_on_the_first_line(
    run_cli: CliRunner, symbolic_cases: Path
) -> None:
    result = run_cli("solve", symbolic_cases / "decay_candidate_correct.json")

    assert result.exit_code == ExitCode.SUCCESS
    assert result.stdout.splitlines()[:2] == [
        "Candidata aprovada: y(t) = y_0*exp(-k*t)",
        "revisão por substituição; adimensional; verificação: passed",
    ]


@pytest.mark.parametrize("output_format", ["text", "json"])
def test_the_same_statement_gives_byte_identical_output(
    run_cli: CliRunner, symbolic_cases: Path, output_format: str
) -> None:
    arguments = ("solve", symbolic_cases / "decay_initial_value.json", "--format", output_format)

    assert run_cli(*arguments).stdout == run_cli(*arguments).stdout
