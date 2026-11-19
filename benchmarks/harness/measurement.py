from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from benchmarks.harness.bench_session import BenchSession
from benchmarks.harness.cold_runs import refuse_in_new_process, solve_in_new_process
from benchmarks.harness.environment import (
    describe_machine,
    pin_linear_algebra_threads,
    profile_differences,
)
from benchmarks.harness.precision import PrecisionLedger
from benchmarks.harness.protocol import (
    MeasurementProtocol,
    RefusedRequest,
    Workload,
    load_profile,
    load_workloads,
)
from benchmarks.harness.report import (
    REPORT_SCHEMA,
    REPORT_SCHEMA_VERSION,
    BenchmarkReport,
    LinearAlgebraLibrary,
    RefusalMeasurement,
    Software,
    StagedMeasurement,
    TimedRuns,
    WarmMeasurement,
    WorkloadMeasurement,
)
from benchmarks.harness.staged_runs import StagedPipeline
from benchmarks.harness.stages import STAGES
from benchmarks.harness.statistics import summarize
from benchmarks.harness.targets import evaluate_targets
from quantum_calculator.adapters.execution.runtime_environment import RuntimeEnvironmentProbe


class RefusalMismatchError(Exception):
    pass


class WorkloadMeter:
    def __init__(
        self,
        root: Path,
        command: str,
        protocol: MeasurementProtocol,
        bench: BenchSession,
        pipeline: StagedPipeline,
    ) -> None:
        self._root = root
        self._command = command
        self._protocol = protocol
        self._bench = bench
        self._pipeline = pipeline

    def measure(self, workload: Workload) -> WorkloadMeasurement:
        ledger = PrecisionLedger(workload)
        return WorkloadMeasurement(
            identifier=workload["identifier"],
            title=workload["title"],
            input=workload["input"],
            cold=self._cold(workload, ledger),
            warm=self._warm(workload, ledger),
            staged=self._staged(workload, ledger),
            precision=ledger.report(),
        )

    def _cold(self, workload: Workload, ledger: PrecisionLedger) -> TimedRuns:
        seconds = []
        for _ in range(self._protocol["cold_runs"]):
            run = solve_in_new_process(self._command, self._root / workload["input"])
            ledger.check(run.record)
            seconds.append(run.seconds)
        return _timed(seconds)

    def _warm(self, workload: Workload, ledger: PrecisionLedger) -> WarmMeasurement:
        source = (self._root / workload["input"]).read_bytes()
        seconds = []
        peak = 0
        for _ in range(self._protocol["warmup_runs"] + self._protocol["measured_runs"]):
            run = self._bench.calculate(source)
            ledger.check(run.record)
            seconds.append(run.seconds)
            peak = max(peak, run.worker_peak_rss_bytes)
        measured = seconds[self._protocol["warmup_runs"] :]
        return WarmMeasurement(
            runs_seconds=measured, summary=summarize(measured), worker_peak_rss_bytes=peak
        )

    def _staged(self, workload: Workload, ledger: PrecisionLedger) -> StagedMeasurement:
        source = (self._root / workload["input"]).read_bytes()
        runs = []
        for _ in range(self._protocol["warmup_runs"] + self._protocol["measured_runs"]):
            run = self._pipeline.run(source)
            ledger.check(run.record)
            runs.append(run)
        measured = runs[self._protocol["warmup_runs"] :]
        return StagedMeasurement(
            stages={
                stage: _timed([run.stage_seconds[stage] for run in measured]) for stage in STAGES
            },
            total=_timed([sum(run.stage_seconds.values()) for run in measured]),
            worker_peak_rss_bytes=max(run.worker_peak_rss_bytes for run in runs),
        )


def measure(root: Path, command: str, announce: Callable[[str], None]) -> BenchmarkReport:
    profile = load_profile(root)
    index = load_workloads(root)
    pin_linear_algebra_threads(profile["execution"]["linear_algebra_threads"])
    with BenchSession(command) as bench:
        meter = WorkloadMeter(root, command, profile["protocol"], bench, StagedPipeline())
        workloads = []
        for workload in index["workloads"]:
            announce(workload["identifier"])
            workloads.append(meter.measure(workload))
    refusals = [_refusal(root, command, request) for request in index["refused_requests"]]
    machine = describe_machine()
    return BenchmarkReport(
        schema=REPORT_SCHEMA,
        schema_version=REPORT_SCHEMA_VERSION,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        profile=profile,
        machine=machine,
        software=_software(),
        profile_differences=profile_differences(machine, profile["machine"]),
        workloads=workloads,
        refused_requests=refusals,
        targets=evaluate_targets(profile["targets"], workloads),
    )


def _refusal(root: Path, command: str, request: RefusedRequest) -> RefusalMeasurement:
    refused = refuse_in_new_process(command, root / request["input"])
    codes = [diagnostic.get("code") for diagnostic in refused.diagnostics]
    if refused.exit_code != request["exit_code"] or request["diagnostic"] not in codes:
        raise RefusalMismatchError(
            f"request {request['identifier']} ended with exit code {refused.exit_code} and "
            f"diagnostics {codes}, expected exit code {request['exit_code']} and "
            f"{request['diagnostic']}"
        )
    return RefusalMeasurement(
        identifier=request["identifier"],
        title=request["title"],
        input=request["input"],
        exit_code=refused.exit_code,
        seconds=refused.seconds,
        diagnostics=refused.diagnostics,
    )


def _timed(seconds: list[float]) -> TimedRuns:
    return TimedRuns(runs_seconds=seconds, summary=summarize(seconds))


def _software() -> Software:
    manifest = RuntimeEnvironmentProbe().describe()
    return Software(
        package=manifest.package_name,
        version=manifest.package_version,
        dependencies={dependency.name: dependency.version for dependency in manifest.dependencies},
        linear_algebra=[
            LinearAlgebraLibrary(
                consumer=library.consumer,
                interface=library.interface,
                name=library.name,
                version=library.version,
            )
            for library in manifest.linear_algebra
        ],
    )
