from typing import Literal, TypedDict

MATRIX_SCHEMA = "qualification_case_matrix"
REPORT_SCHEMA = "qualification_reproduction_report"
SCHEMA_VERSION = "1.0"

type Command = Literal["solve", "validate"]
type Comparison = Literal["absolute", "relative"]


class ExpectedValue(TypedDict):
    name: str
    expected: float
    tolerance: float
    comparison: Comparison


class Refusal(TypedDict):
    category: str
    code: str
    pointer: str


class Expectation(TypedDict):
    identifier: str
    family: str
    card: str
    input: str
    command: Command
    oracle: str
    exit_code: int
    verification: str | None
    not_passed: list[str]
    values: list[ExpectedValue]
    texts: dict[str, str]
    refusal: Refusal | None


class Observation(TypedDict):
    exit_code: int
    card: str | None
    verification: str | None
    not_passed: list[str]
    values: dict[str, float]
    texts: dict[str, str]
    refusals: list[Refusal]


class MatrixCase(TypedDict):
    expectation: Expectation
    observation: Observation
    disagreements: list[str]


class CardCoverage(TypedDict):
    card: str
    version: str
    method: str
    example: str
    answered_cases: list[str]
    refused_cases: list[str]
    gaps: list[str]


class CaseMatrix(TypedDict):
    schema: str
    schema_version: str
    generated_at: str
    calculator: str
    environment: dict[str, object]
    catalog_version: str
    cases: list[MatrixCase]
    coverage: list[CardCoverage]


class ReproducedCase(TypedDict):
    identifier: str
    observation: Observation
    differences: list[str]


class VersionDivergence(TypedDict):
    subject: str
    base: str | None
    other: str | None


class ReproducedPackage(TypedDict):
    package: str
    sha256: str
    imported_state: str
    rerun_state: str
    received_state: str
    version_divergences: list[VersionDivergence]
    differences: list[str]


class Homologation(TypedDict):
    calculator: str
    generated_at: str
    catalog_version: str


class ReproductionReport(TypedDict):
    schema: str
    schema_version: str
    generated_at: str
    homologated: Homologation
    calculator: str
    environment: dict[str, object]
    catalog_differences: list[str]
    cases: list[ReproducedCase]
    packages: list[ReproducedPackage]
