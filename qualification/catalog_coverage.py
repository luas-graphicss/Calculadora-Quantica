from collections.abc import Sequence

from qualification.calculator import Catalog
from qualification.documents import CardCoverage, CaseMatrix, Expectation

_SOLVE = "solve"
_NO_EXAMPLE = "the catalog example is not a case with an independent oracle"
_NO_ORACLE = "no answered case with an independent oracle"
_NO_REFUSAL = "no refused case showing the behaviour outside the domain"


def card_coverage(catalog: Catalog, expectations: Sequence[Expectation]) -> list[CardCoverage]:
    solved = [expectation for expectation in expectations if expectation["command"] == _SOLVE]
    coverage = []
    for card in catalog["cards"]:
        cases = [expectation for expectation in solved if expectation["card"] == card["identifier"]]
        answered = [case for case in cases if case["refusal"] is None]
        refused = [case["identifier"] for case in cases if case["refusal"] is not None]
        gaps = []
        if card["example"] not in {case["input"] for case in answered}:
            gaps.append(_NO_EXAMPLE)
        if not answered:
            gaps.append(_NO_ORACLE)
        if not refused:
            gaps.append(_NO_REFUSAL)
        coverage.append(
            CardCoverage(
                card=card["identifier"],
                version=card["version"],
                method=card["method"]["identifier"],
                example=card["example"],
                answered_cases=[case["identifier"] for case in answered],
                refused_cases=refused,
                gaps=gaps,
            )
        )
    return coverage


def catalog_differences(matrix: CaseMatrix, catalog: Catalog) -> list[str]:
    homologated = {
        coverage["card"]: (coverage["version"], coverage["method"])
        for coverage in matrix["coverage"]
    }
    installed = {
        card["identifier"]: (card["version"], card["method"]["identifier"])
        for card in catalog["cards"]
    }
    differences = [
        f"card {card} is homologated but not installed" for card in homologated.keys() - installed
    ]
    differences += [
        f"card {card} is installed but not homologated" for card in installed.keys() - homologated
    ]
    differences += [
        f"card {card} is installed as version {installed[card][0]} with method "
        f"{installed[card][1]}, homologated as version {homologated[card][0]} with method "
        f"{homologated[card][1]}"
        for card in sorted(homologated.keys() & installed.keys())
        if homologated[card] != installed[card]
    ]
    if matrix["catalog_version"] != catalog["version"]:
        differences.append(
            f"catalog version {catalog['version']}, homologated {matrix['catalog_version']}"
        )
    return sorted(differences)
