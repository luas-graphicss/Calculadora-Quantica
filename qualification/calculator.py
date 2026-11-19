import json
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict

from qualification.documents import Command, Observation, Refusal

_SECONDS = 900.0
_PASSED = "passed"


class CatalogCard(TypedDict):
    identifier: str
    version: str
    method: dict[str, str]
    example: str


class Catalog(TypedDict):
    version: str
    cards: list[CatalogCard]


class Observed(TypedDict):
    observation: Observation
    environment: dict[str, object] | None


class Calculator:
    def __init__(self, command: str) -> None:
        self._command = command

    def version(self) -> str:
        return self._run("--version").stdout.decode("utf-8").strip()

    def catalog(self) -> Catalog:
        catalog: Catalog = json.loads(self._run("catalog", "--format", "json").stdout)
        return catalog

    def observe(self, command: Command, document: bytes) -> Observed:
        with tempfile.TemporaryDirectory(prefix="qcalc-qualification-") as directory:
            source = Path(directory) / "input.json"
            source.write_bytes(document)
            completed = self._run(command, str(source), "--format", "json")
        if completed.stdout:
            answered = json.loads(completed.stdout)
            return Observed(
                observation=_answered(completed.returncode, answered),
                environment=answered.get("environment"),
            )
        return Observed(
            observation=_refused(completed.returncode, completed.stderr), environment=None
        )

    def _run(self, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(  # noqa: S603 - the command is the qcalc under qualification, with fixed arguments
            [self._command, *arguments], capture_output=True, check=False, timeout=_SECONDS
        )


def _answered(exit_code: int, document: dict[str, dict[str, object]]) -> Observation:
    result = document.get("result", {})
    problem = document.get("problem", {})
    verification = document.get("verification", {})
    checks = verification.get("checks", [])
    return Observation(
        exit_code=exit_code,
        card=_card(problem),
        verification=_text(verification.get("status")),
        not_passed=sorted(
            str(check["identifier"])
            for check in (checks if isinstance(checks, list) else [])
            if check["status"] != _PASSED
        ),
        values=_values(result),
        texts=_texts(result, problem),
        refusals=[],
    )


def _refused(exit_code: int, diagnostics: bytes) -> Observation:
    try:
        rejection = json.loads(diagnostics)
    except ValueError:
        rejection = {"diagnostics": []}
    return Observation(
        exit_code=exit_code,
        card=None,
        verification=None,
        not_passed=[],
        values={},
        texts={},
        refusals=[
            Refusal(
                category=diagnostic["category"],
                code=diagnostic["code"],
                pointer=diagnostic["pointer"],
            )
            for diagnostic in rejection["diagnostics"]
        ],
    )


def _card(problem: dict[str, object]) -> str | None:
    card = problem.get("card")
    return _text(card.get("identifier")) if isinstance(card, dict) else None


def _values(result: dict[str, object]) -> dict[str, float]:
    answers = result.get("answers")
    if isinstance(answers, list):
        return {str(answer["name"]): float(answer["value"]) for answer in answers}
    value = result.get("value")
    if isinstance(value, dict) and "quantity" in result:
        return {str(result["quantity"]): float(value["decimal"])}
    return {}


def _texts(result: dict[str, object], problem: dict[str, object]) -> dict[str, str]:
    texts = {}
    answer = result.get("answer")
    if isinstance(answer, dict):
        texts["answer"] = str(answer["text"])
    uncertainty = result.get("uncertainty")
    if isinstance(uncertainty, dict) and "standard_uncertainty" in uncertainty:
        texts["standard_uncertainty"] = str(uncertainty["standard_uncertainty"]["decimal"])
        texts["relative_standard_uncertainty"] = str(uncertainty["relative_standard_uncertainty"])
    statement = problem.get("statement")
    if isinstance(statement, dict) and "structure" in statement:
        texts["structure"] = str(statement["structure"])
    return texts


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None
