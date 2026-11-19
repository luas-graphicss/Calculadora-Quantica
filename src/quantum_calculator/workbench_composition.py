import uuid
from dataclasses import dataclass
from functools import lru_cache
from importlib import metadata
from pathlib import Path

from quantum_calculator.adapters.execution.runtime_environment import PACKAGE_NAME
from quantum_calculator.adapters.execution.serial_run_queue import SerialRunQueue
from quantum_calculator.adapters.storage.data_directory import (
    ARTIFACTS_DIRECTORY,
    HISTORY_FILE,
    PRIVATE_DIRECTORY,
)
from quantum_calculator.adapters.storage.file_artifacts import FileArtifactStore
from quantum_calculator.adapters.storage.sqlite_runs import SqliteRunRepository
from quantum_calculator.adapters.storage.system_clock import SystemClock
from quantum_calculator.adapters.storage.zip_packages import ZipPackageArchive
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.statements.budget import symbolic_budget
from quantum_calculator.application.workbench.cancel_run import CancelRun
from quantum_calculator.application.workbench.cancellations import RunCancellations
from quantum_calculator.application.workbench.compare_runs import CompareRuns
from quantum_calculator.application.workbench.describe_catalog import (
    DescribeCatalog,
    WorkbenchCatalog,
)
from quantum_calculator.application.workbench.display_answers import DisplayAnswers
from quantum_calculator.application.workbench.execute_run import ExecuteRun
from quantum_calculator.application.workbench.export_package import (
    ExportPackage,
    PackageGenerator,
)
from quantum_calculator.application.workbench.import_package import ImportPackage
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.application.workbench.recover_history import (
    InterruptActiveRuns,
    RecoverHistory,
)
from quantum_calculator.application.workbench.submit_run import SubmitRun
from quantum_calculator.composition import Calculator, build_calculator
from quantum_calculator.domain.workbench.ports import CalculationDocuments
from quantum_calculator.interfaces.serialization.document_calculator import DocumentCalculator
from quantum_calculator.interfaces.serialization.encoding.common_sections import (
    READABLE_OUTPUT_SCHEMA_VERSIONS,
)

_CACHED_TIME_LIMITS = 8


@dataclass(frozen=True, slots=True)
class Workbench:
    catalog: WorkbenchCatalog
    documents: CalculationDocuments
    submit: SubmitRun
    cancel: CancelRun
    history: ReadHistory
    display: DisplayAnswers
    compare: CompareRuns
    export_package: ExportPackage
    import_package: ImportPackage
    recover: RecoverHistory
    interrupt: InterruptActiveRuns
    queue: SerialRunQueue

    def shut_down(self) -> None:
        self.interrupt.execute()
        self.queue.close()


def build_workbench(data_directory: Path) -> Workbench:
    data_directory.mkdir(mode=PRIVATE_DIRECTORY, parents=True, exist_ok=True)
    constants = Codata2022Constants()
    units = SiUnitRegistry(constants)
    runs = SqliteRunRepository(data_directory / HISTORY_FILE)
    artifacts = FileArtifactStore(data_directory / ARTIFACTS_DIRECTORY)
    archive = ZipPackageArchive()
    clock = SystemClock()
    cancellations = RunCancellations()
    version = metadata.version(PACKAGE_NAME)
    documents = DocumentCalculator(_calculator_for)
    queue = SerialRunQueue(ExecuteRun(documents, runs, artifacts, cancellations, clock).execute)
    history = ReadHistory(runs, artifacts)
    return Workbench(
        catalog=DescribeCatalog(units, constants).execute(),
        documents=documents,
        submit=SubmitRun(documents, runs, artifacts, queue, clock, _new_identifier, version),
        cancel=CancelRun(runs, cancellations, clock),
        history=history,
        display=DisplayAnswers(history, units),
        compare=CompareRuns(history, units),
        export_package=ExportPackage(history, archive, PackageGenerator(PACKAGE_NAME, version)),
        import_package=ImportPackage(
            runs, artifacts, archive, _new_identifier, READABLE_OUTPUT_SCHEMA_VERSIONS
        ),
        recover=RecoverHistory(runs, artifacts, clock),
        interrupt=InterruptActiveRuns(runs, cancellations, clock),
        queue=queue,
    )


@lru_cache(maxsize=_CACHED_TIME_LIMITS)
def _calculator_for(wall_seconds: float) -> Calculator:
    return build_calculator(symbolic_budget(wall_seconds))


def _new_identifier() -> str:
    return uuid.uuid4().hex
