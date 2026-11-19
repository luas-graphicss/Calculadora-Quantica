from datetime import UTC, datetime
from pathlib import Path

from qualification.calculator import Calculator
from qualification.catalog_coverage import card_coverage
from qualification.comparison import disagreements_with_oracle
from qualification.corpus import corpus_cases
from qualification.documents import MATRIX_SCHEMA, SCHEMA_VERSION, CaseMatrix, MatrixCase


def build_matrix(root: Path, calculator: Calculator) -> CaseMatrix:
    cases = []
    environment: dict[str, object] = {}
    for case in corpus_cases(root):
        observed = calculator.observe(case.expectation["command"], case.document)
        environment = environment or observed["environment"] or {}
        cases.append(
            MatrixCase(
                expectation=case.expectation,
                observation=observed["observation"],
                disagreements=disagreements_with_oracle(case.expectation, observed["observation"]),
            )
        )
    catalog = calculator.catalog()
    return CaseMatrix(
        schema=MATRIX_SCHEMA,
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        calculator=calculator.version(),
        environment=environment,
        catalog_version=catalog["version"],
        cases=cases,
        coverage=card_coverage(catalog, [case["expectation"] for case in cases]),
    )


def is_homologated(matrix: CaseMatrix) -> bool:
    return not any(case["disagreements"] for case in matrix["cases"]) and not any(
        coverage["gaps"] for coverage in matrix["coverage"]
    )
