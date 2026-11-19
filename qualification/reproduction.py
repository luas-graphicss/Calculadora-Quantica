from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from qualification.bench_client import BenchClient
from qualification.calculator import Calculator
from qualification.catalog_coverage import catalog_differences
from qualification.comparison import differences_from_homologation
from qualification.corpus import corpus_cases
from qualification.documents import (
    REPORT_SCHEMA,
    SCHEMA_VERSION,
    CaseMatrix,
    Homologation,
    Observation,
    ReproducedCase,
    ReproducedPackage,
    ReproductionReport,
)
from qualification.witness_packages import reproduce_package

_MISSING = Observation(
    exit_code=-1, card=None, verification=None, not_passed=[], values={}, texts={}, refusals=[]
)


def reproduce(
    root: Path, matrix: CaseMatrix, command: str, packages: Sequence[Path]
) -> ReproductionReport:
    calculator = Calculator(command)
    documents = {case.expectation["identifier"]: case.document for case in corpus_cases(root)}
    cases = []
    environment: dict[str, object] = {}
    for homologated in matrix["cases"]:
        expectation = homologated["expectation"]
        document = documents.get(expectation["identifier"])
        if document is None:
            cases.append(
                ReproducedCase(
                    identifier=expectation["identifier"],
                    observation=_MISSING,
                    differences=["the case is missing from the corpus of this installation"],
                )
            )
            continue
        observed = calculator.observe(expectation["command"], document)
        environment = environment or observed["environment"] or {}
        cases.append(
            ReproducedCase(
                identifier=expectation["identifier"],
                observation=observed["observation"],
                differences=differences_from_homologation(
                    expectation, homologated["observation"], observed["observation"]
                ),
            )
        )
    return ReproductionReport(
        schema=REPORT_SCHEMA,
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        homologated=Homologation(
            calculator=matrix["calculator"],
            generated_at=matrix["generated_at"],
            catalog_version=matrix["catalog_version"],
        ),
        calculator=calculator.version(),
        environment=environment,
        catalog_differences=catalog_differences(matrix, calculator.catalog()),
        cases=cases,
        packages=_reproduced_packages(command, packages),
    )


def is_reproduced(report: ReproductionReport) -> bool:
    return (
        not report["catalog_differences"]
        and not any(case["differences"] for case in report["cases"])
        and not any(package["differences"] for package in report["packages"])
    )


def _reproduced_packages(command: str, packages: Sequence[Path]) -> list[ReproducedPackage]:
    if not packages:
        return []
    with BenchClient(command) as bench, BenchClient(command) as receiver:
        return [reproduce_package(bench, package, receiver) for package in packages]
