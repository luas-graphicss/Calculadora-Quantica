import json
import time
from dataclasses import dataclass
from functools import partial

from benchmarks.harness.precision import NumericalRecord
from benchmarks.harness.stages import STAGES
from benchmarks.harness.worker_task import solve_and_verify_measured
from quantum_calculator.adapters.execution.process_executor import ProcessExecutor
from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.numerical.validator import NumericalValidator
from quantum_calculator.application.statements.budget import DEFAULT_SYMBOLIC_BUDGET
from quantum_calculator.application.workbench.canonical_documents import canonical_json
from quantum_calculator.catalog.listing import CATALOG_VERSION
from quantum_calculator.catalog.numerical_catalog import (
    HOMOLOGATED_NUMERICAL_CARDS,
    NumericalCatalog,
)
from quantum_calculator.domain.execution import NeverCancelled
from quantum_calculator.domain.numerical.report import NumericalPlan, NumericalRunRecord
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.interfaces.serialization.decoding.input_decoder import decode_input
from quantum_calculator.interfaces.serialization.encoding.numerical_documents import (
    NumericalDocumentEncoder,
)
from quantum_calculator.method_registry import numerical_methods


@dataclass(frozen=True, slots=True)
class StagedRun:
    stage_seconds: dict[str, float]
    record: NumericalRecord
    worker_peak_rss_bytes: int


class StagedPipeline:
    def __init__(self) -> None:
        constants = Codata2022Constants()
        self._units = SiUnitRegistry(constants)
        self._constants_edition = constants.label
        self._cards = frozenset(card.identifier for card in HOMOLOGATED_NUMERICAL_CARDS)
        self._validator = NumericalValidator(
            NumericalCatalog(HOMOLOGATED_NUMERICAL_CARDS), self._units, constants
        )
        self._methods = numerical_methods()
        self._executor = ProcessExecutor()
        self._environment = RuntimeEnvironmentProbe()
        self._encoder = NumericalDocumentEncoder(self._units)

    def run(self, source: bytes) -> StagedRun:
        submitted = time.perf_counter()
        spec = decode_input(source, self._cards)
        if not isinstance(spec, NumericalSpec):
            raise TypeError("the staged pipeline measures numerical cards only")
        problem = self._validator.validate(spec)
        interpreted = time.perf_counter()
        plan = NumericalPlan(problem.context.card.method, DEFAULT_SYMBOLIC_BUDGET)
        measured = self._executor.run(
            partial(solve_and_verify_measured, self._methods[plan.method.identifier], problem),
            plan.budget,
            NeverCancelled(),
        )
        calculated = time.perf_counter()
        document = canonical_json(
            self._encoder.run_record(
                NumericalRunRecord(
                    problem=problem,
                    plan=plan,
                    report=measured.outcome.report,
                    verification=measured.outcome.verification,
                    catalog_version=CATALOG_VERSION,
                    constants_edition=self._constants_edition,
                    unit_registry_version=self._units.version,
                    environment=self._environment.describe(),
                )
            )
        )
        reported = time.perf_counter()
        record: NumericalRecord = json.loads(document)
        return StagedRun(
            stage_seconds=dict(
                zip(
                    STAGES,
                    (
                        interpreted - submitted,
                        calculated
                        - interpreted
                        - measured.solver_seconds
                        - measured.verification_seconds,
                        measured.solver_seconds,
                        measured.verification_seconds,
                        reported - calculated,
                    ),
                    strict=True,
                )
            ),
            record=record,
            worker_peak_rss_bytes=measured.peak_rss_bytes,
        )
