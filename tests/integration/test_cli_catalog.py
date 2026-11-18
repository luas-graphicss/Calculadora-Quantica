import json

from quantum_calculator.catalog.listing import CATALOG_VERSION, catalog_entries
from quantum_calculator.domain.methods import ResultNature
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
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


def test_no_method_awaiting_homologation_is_listed_as_available(run_cli: CliRunner) -> None:
    cards = json.loads(run_cli("catalog", "--format", "json").stdout)["cards"]

    assert {card["method"]["nature"] for card in cards} == {ResultNature.EXACT.value}
