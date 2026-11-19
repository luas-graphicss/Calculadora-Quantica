import json

from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS
from quantum_calculator.catalog.listing import CATALOG_VERSION, catalog_entries
from quantum_calculator.catalog.numerical_catalog import HOMOLOGATED_NUMERICAL_CARDS
from quantum_calculator.catalog.statement_catalog import HOMOLOGATED_STATEMENT_CARDS
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from quantum_calculator.method_registry import (
    numerical_methods,
    problem_methods,
    statement_methods,
)
from support.cli import CliRunner


def test_catalog_lists_every_homologated_card_with_its_version(run_cli: CliRunner) -> None:
    result = run_cli("catalog")

    entries = catalog_entries()
    assert result.exit_code == ExitCode.SUCCESS
    assert result.stdout.splitlines()[0] == (
        f"Catálogo {CATALOG_VERSION}: {len(entries)} fichas homologadas"
    )
    assert all(f"\n{entry.identifier} {entry.version}\n" in result.stdout for entry in entries)


def test_catalog_document_versions_each_card_by_area_type_domain_and_method(
    run_cli: CliRunner,
) -> None:
    document = json.loads(run_cli("catalog", "--format", "json").stdout)

    cards = document["cards"]
    assert document["document"] == "catalog"
    assert document["version"] == CATALOG_VERSION
    assert [card["identifier"] for card in cards] == [
        entry.identifier for entry in catalog_entries()
    ]
    assert all(
        card["version"] and card["area"] and card["problem_type"] and card["domain"]
        for card in cards
    )
    assert all(card["method"]["identifier"] and card["limitations"] for card in cards)


def test_every_listed_method_is_homologated_and_says_whether_it_approximates(
    run_cli: CliRunner, constants: Codata2022Constants
) -> None:
    cards = json.loads(run_cli("catalog", "--format", "json").stdout)["cards"]

    homologated = {*problem_methods(constants), *statement_methods(), *numerical_methods()}
    natures = {card["identifier"]: card["method"]["nature"] for card in cards}
    assert {card["method"]["identifier"] for card in cards} == homologated
    assert {natures[card.identifier] for card in HOMOLOGATED_NUMERICAL_CARDS} == {
        ResultNature.APPROXIMATE.value
    }
    assert {
        natures[card.identifier] for card in (*HOMOLOGATED_CARDS, *HOMOLOGATED_STATEMENT_CARDS)
    } == {ResultNature.EXACT.value}
