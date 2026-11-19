import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from qualification.corpus_files import (
    ClosedFormOracle,
    NotationCorpus,
    NotationItem,
    NumericalAnswer,
    read_closed_form_oracle,
    read_notation_corpus,
    read_numerical_expectations,
    read_refused_expectations,
    read_symbolic_expectations,
)
from qualification.documents import Command, Expectation, ExpectedValue, Refusal

CORPUS_DIRECTORY = "reference_cases"

_VERIFICATION_NOT_PASSED = 5
_EXIT_CODE_BY_CATEGORY = {
    "invalid_input": 3,
    "unsupported_problem": 4,
    "ambiguous_input": 6,
    "budget_exceeded": 7,
    "non_convergent": 9,
}
_PASSED = "passed"
_ACCEPTED = "accepted"
_FAMILIES_WITH_REFUSALS = ("quantum", "symbolic", "numerical")
_INPUT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class CorpusCase:
    expectation: Expectation
    document: bytes


class _Outline(TypedDict):
    identifier: str
    family: str
    card: str
    input: str
    command: Command
    oracle: str


def corpus_cases(root: Path) -> list[CorpusCase]:
    corpus = root / CORPUS_DIRECTORY
    return [
        *_closed_form_cases(root, corpus / "quantum"),
        *_symbolic_cases(root, corpus / "symbolic"),
        *_numerical_cases(root, corpus / "numerical"),
        *(
            case
            for family in _FAMILIES_WITH_REFUSALS
            for case in _refused_cases(root, corpus / family)
        ),
        *_notation_cases(root, corpus / "notation" / "corpus.json"),
    ]


def _closed_form_cases(root: Path, directory: Path) -> Iterator[CorpusCase]:
    for oracle_file in sorted(directory.glob("*.expected.json")):
        oracle = read_closed_form_oracle(oracle_file)
        source = directory / oracle["case"]
        yield _answered(
            _outline(root, source, "solve", _closed_form_description(oracle)),
            source.read_bytes(),
            verification=_PASSED,
            values=[
                ExpectedValue(
                    name=oracle["quantity"],
                    expected=float(oracle["nominal_value"]),
                    tolerance=float(oracle["absolute_tolerance"]),
                    comparison="absolute",
                )
            ],
            texts=_uncertainty_texts(oracle),
        )


def _closed_form_description(oracle: ClosedFormOracle) -> str:
    parts = (
        oracle["derivation"],
        oracle.get("tolerance_rationale"),
        oracle.get("uncertainty_rationale"),
    )
    return " ".join(part for part in parts if part)


def _uncertainty_texts(oracle: ClosedFormOracle) -> dict[str, str]:
    if "standard_uncertainty" not in oracle or "relative_standard_uncertainty" not in oracle:
        return {}
    return {
        "standard_uncertainty": oracle["standard_uncertainty"],
        "relative_standard_uncertainty": oracle["relative_standard_uncertainty"],
    }


def _symbolic_cases(root: Path, directory: Path) -> Iterator[CorpusCase]:
    for case in read_symbolic_expectations(directory / "expectations.json")["cases"]:
        source = directory / case["file"]
        oracle = (
            f"{case['derivation']} Resposta do oráculo: {case['answer']}, comparada por "
            "equivalência matemática."
        )
        yield _answered(
            _outline(root, source, "solve", oracle),
            source.read_bytes(),
            verification=case["verification"],
            not_passed=case["failed_checks"],
        )


def _numerical_cases(root: Path, directory: Path) -> Iterator[CorpusCase]:
    for case in read_numerical_expectations(directory / "expectations.json")["cases"]:
        source = directory / case["file"]
        yield _answered(
            _outline(root, source, "solve", case["oracle"]),
            source.read_bytes(),
            verification=case["verification"],
            not_passed=case["not_passed"],
            values=[_expected_value(answer) for answer in case["answers"]],
        )


def _refused_cases(root: Path, directory: Path) -> Iterator[CorpusCase]:
    refused = directory / "rejected"
    for case in read_refused_expectations(refused / "expectations.json")["cases"]:
        source = refused / case["file"]
        outline = _outline(root, source, "solve", case.get("reason") or case.get("defect", ""))
        yield _refused(
            outline,
            source.read_bytes(),
            Refusal(category=case["category"], code=case["code"], pointer=case["pointer"]),
        )


def _notation_cases(root: Path, corpus_file: Path) -> Iterator[CorpusCase]:
    corpus = read_notation_corpus(corpus_file)
    location = corpus_file.relative_to(root).as_posix()
    items = {item["id"]: item for item in corpus["items"]}
    for item in corpus["items"]:
        expected = item["expected"]
        outline = _Outline(
            identifier=f"notation/{item['id']}",
            family="notation",
            card=expected.get("card", item.get("problem", "")),
            input=f"{location}#{item['id']}",
            command="validate",
            oracle=" ".join(part for part in (item["intent"], item.get("reason")) if part),
        )
        document = _notation_document(corpus, item)
        if expected["classification"] == _ACCEPTED:
            labelled = items[item.get("same_problem_as", item["id"])]["expected"]
            yield _answered(outline, document, texts={"structure": labelled["structure"]})
        else:
            yield _refused(
                outline,
                document,
                Refusal(
                    category=expected["classification"],
                    code=expected["code"],
                    pointer=expected["pointer"],
                ),
            )


def _notation_document(corpus: NotationCorpus, item: NotationItem) -> bytes:
    document: dict[str, object] = {
        "schema_version": _INPUT_SCHEMA_VERSION,
        "notation": item["notation"],
        "statement": item["statement"],
        "symbols": corpus["symbol_sets"][item["symbols"]],
    }
    if "problem" in item:
        document["problem"] = item["problem"]
    if "conditions" in item:
        document["conditions"] = item["conditions"]
    if "candidate" in item:
        document["candidate"] = item["candidate"]
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


def _outline(root: Path, source: Path, command: Command, oracle: str) -> _Outline:
    return _Outline(
        identifier=f"{source.parent.relative_to(root / CORPUS_DIRECTORY).as_posix()}/{source.stem}",
        family=source.relative_to(root / CORPUS_DIRECTORY).parts[0],
        card=_declared_card(source),
        input=source.relative_to(root).as_posix(),
        command=command,
        oracle=oracle,
    )


def _answered(
    outline: _Outline,
    document: bytes,
    *,
    verification: str | None = None,
    not_passed: list[str] | None = None,
    values: list[ExpectedValue] | None = None,
    texts: dict[str, str] | None = None,
) -> CorpusCase:
    is_approved = verification in (None, _PASSED)
    return CorpusCase(
        Expectation(
            **outline,
            exit_code=0 if is_approved else _VERIFICATION_NOT_PASSED,
            verification=verification,
            not_passed=sorted(not_passed or []),
            values=values or [],
            texts=texts or {},
            refusal=None,
        ),
        document,
    )


def _refused(outline: _Outline, document: bytes, refusal: Refusal) -> CorpusCase:
    return CorpusCase(
        Expectation(
            **outline,
            exit_code=_EXIT_CODE_BY_CATEGORY[refusal["category"]],
            verification=None,
            not_passed=[],
            values=[],
            texts={},
            refusal=refusal,
        ),
        document,
    )


def _expected_value(answer: NumericalAnswer) -> ExpectedValue:
    if "relative_tolerance" in answer:
        return ExpectedValue(
            name=answer["name"],
            expected=answer["expected"],
            tolerance=answer["relative_tolerance"],
            comparison="relative",
        )
    return ExpectedValue(
        name=answer["name"],
        expected=answer["expected"],
        tolerance=answer["absolute_tolerance"],
        comparison="absolute",
    )


def _declared_card(source: Path) -> str:
    try:
        document = json.loads(source.read_bytes())
    except ValueError:
        return ""
    card = document.get("problem") if isinstance(document, dict) else None
    return card if isinstance(card, str) else ""
