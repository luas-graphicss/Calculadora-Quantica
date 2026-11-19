from qualification.calculator import Catalog, CatalogCard
from qualification.catalog_coverage import card_coverage, catalog_differences
from qualification.documents import CardCoverage, CaseMatrix, Expectation, Refusal

_CARD = "quantum.infinite_square_well.energy_level"
_EXAMPLE = "reference_cases/quantum/electron_box_1nm.json"


def _catalog(version: str = "1.4.0", method: str = "closed_form") -> Catalog:
    card = CatalogCard(
        identifier=_CARD, version="1.0.0", method={"identifier": method}, example=_EXAMPLE
    )
    return Catalog(version=version, cards=[card])


def _case(identifier: str, source: str, *, is_refused: bool = False) -> Expectation:
    refusal = Refusal(category="invalid_input", code="dimension_mismatch", pointer="/parameters")
    return Expectation(
        identifier=identifier,
        family="quantum",
        card=_CARD,
        input=source,
        command="solve",
        oracle="E_n = n^2 h^2 / (8 m L^2)",
        exit_code=3 if is_refused else 0,
        verification=None if is_refused else "passed",
        not_passed=[],
        values=[],
        texts={},
        refusal=refusal if is_refused else None,
    )


def _matrix(coverage: list[CardCoverage], catalog_version: str = "1.4.0") -> CaseMatrix:
    return CaseMatrix(
        schema="qualification_case_matrix",
        schema_version="1.0",
        generated_at="2026-11-19T12:00:00+00:00",
        calculator="qcalc 1.0.0rc1",
        environment={},
        catalog_version=catalog_version,
        cases=[],
        coverage=coverage,
    )


def test_a_card_with_its_example_an_oracle_and_a_refusal_has_no_gap() -> None:
    cases = [
        _case("quantum/electron_box_1nm", _EXAMPLE),
        _case("quantum/rejected/width_in_seconds", "rejected.json", is_refused=True),
    ]

    (coverage,) = card_coverage(_catalog(), cases)

    assert coverage["gaps"] == []
    assert coverage["answered_cases"] == ["quantum/electron_box_1nm"]
    assert coverage["refused_cases"] == ["quantum/rejected/width_in_seconds"]


def test_a_card_without_cases_names_every_missing_piece() -> None:
    (coverage,) = card_coverage(_catalog(), [])

    assert coverage["gaps"] == [
        "the catalog example is not a case with an independent oracle",
        "no answered case with an independent oracle",
        "no refused case showing the behaviour outside the domain",
    ]


def test_a_validation_only_case_does_not_cover_a_card() -> None:
    validated = _case("notation/product-rule", _EXAMPLE)
    validated["command"] = "validate"

    (coverage,) = card_coverage(_catalog(), [validated])

    assert "no answered case with an independent oracle" in coverage["gaps"]


def test_the_same_catalog_has_no_difference_from_the_homologation() -> None:
    homologated = _matrix(card_coverage(_catalog(), []))

    assert catalog_differences(homologated, _catalog()) == []


def test_a_card_installed_with_another_method_is_reported() -> None:
    homologated = _matrix(card_coverage(_catalog(), []))

    found = catalog_differences(homologated, _catalog(version="1.5.0", method="another_method"))

    assert found == [
        f"card {_CARD} is installed as version 1.0.0 with method another_method, homologated "
        "as version 1.0.0 with method closed_form",
        "catalog version 1.5.0, homologated 1.4.0",
    ]


def test_a_card_missing_from_the_installation_is_reported() -> None:
    homologated = _matrix(card_coverage(_catalog(), []))

    found = catalog_differences(homologated, Catalog(version="1.4.0", cards=[]))

    assert found == [f"card {_CARD} is homologated but not installed"]
