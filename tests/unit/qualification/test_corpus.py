import json
from collections import Counter
from pathlib import Path

from qualification.corpus import corpus_cases


def test_every_file_of_the_corpus_becomes_one_case(repository_root: Path) -> None:
    cases = corpus_cases(repository_root)
    corpus = repository_root / "reference_cases"
    inputs = [
        path
        for family in ("quantum", "symbolic", "numerical")
        for path in (corpus / family).rglob("*.json")
        if not path.name.endswith(("expected.json", "expectations.json"))
    ]
    statements = json.loads((corpus / "notation" / "corpus.json").read_text("utf-8"))["items"]

    assert len(cases) == len(inputs) + len(statements)
    assert len({case.expectation["identifier"] for case in cases}) == len(cases)


def test_every_case_states_its_oracle_and_what_must_come_out(repository_root: Path) -> None:
    for case in corpus_cases(repository_root):
        expectation = case.expectation
        assert expectation["oracle"], expectation["identifier"]
        is_refused = expectation["refusal"] is not None
        assert is_refused == (expectation["exit_code"] not in (0, 5)), expectation["identifier"]


def test_the_witness_problem_is_compared_with_its_closed_form(repository_root: Path) -> None:
    cases = {case.expectation["identifier"]: case for case in corpus_cases(repository_root)}

    witness = cases["quantum/electron_box_1nm"].expectation

    assert witness["card"] == "quantum.infinite_square_well.energy_level"
    assert [(value["name"], value["expected"]) for value in witness["values"]] == [
        ("energy", 0.3760301621)
    ]
    assert 0 < witness["values"][0]["tolerance"] <= 1e-9


def test_an_equivalent_notation_is_held_to_the_tree_of_its_reference(
    repository_root: Path,
) -> None:
    corpus = json.loads(
        (repository_root / "reference_cases" / "notation" / "corpus.json").read_text("utf-8")
    )
    items = {item["id"]: item for item in corpus["items"]}
    cases = {case.expectation["identifier"]: case for case in corpus_cases(repository_root)}
    equivalent = next(item for item in corpus["items"] if "same_problem_as" in item)

    expectation = cases[f"notation/{equivalent['id']}"].expectation

    assert expectation["command"] == "validate"
    assert expectation["texts"] == {
        "structure": items[equivalent["same_problem_as"]]["expected"]["structure"]
    }


def test_the_corpus_covers_the_four_families(repository_root: Path) -> None:
    families = Counter(case.expectation["family"] for case in corpus_cases(repository_root))

    assert set(families) == {"quantum", "symbolic", "numerical", "notation"}
    assert all(count > 0 for count in families.values())
