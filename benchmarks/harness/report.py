from typing import TypedDict

from benchmarks.harness.environment import Machine, ProfileDifference
from benchmarks.harness.precision import PrecisionReport
from benchmarks.harness.protocol import ReferenceProfile
from benchmarks.harness.statistics import Summary

REPORT_SCHEMA = "benchmark_report"
REPORT_SCHEMA_VERSION = "1.0"


class TimedRuns(TypedDict):
    runs_seconds: list[float]
    summary: Summary


class WarmMeasurement(TypedDict):
    runs_seconds: list[float]
    summary: Summary
    worker_peak_rss_bytes: int


class StagedMeasurement(TypedDict):
    stages: dict[str, TimedRuns]
    total: TimedRuns
    worker_peak_rss_bytes: int


class WorkloadMeasurement(TypedDict):
    identifier: str
    title: str
    input: str
    cold: TimedRuns
    warm: WarmMeasurement
    staged: StagedMeasurement
    precision: PrecisionReport


class RefusalMeasurement(TypedDict):
    identifier: str
    title: str
    input: str
    exit_code: int
    seconds: float
    diagnostics: list[dict[str, object]]


class TargetVerdict(TypedDict):
    workload: str
    warm_p95_seconds: float
    warm_p95_limit_seconds: float
    worker_peak_rss_mebibytes: float
    worker_peak_rss_limit_mebibytes: int
    met: bool


class LinearAlgebraLibrary(TypedDict):
    consumer: str
    interface: str
    name: str
    version: str


class Software(TypedDict):
    package: str
    version: str
    dependencies: dict[str, str]
    linear_algebra: list[LinearAlgebraLibrary]


class BenchmarkReport(TypedDict):
    schema: str
    schema_version: str
    generated_at: str
    profile: ReferenceProfile
    machine: Machine
    software: Software
    profile_differences: list[ProfileDifference]
    workloads: list[WorkloadMeasurement]
    refused_requests: list[RefusalMeasurement]
    targets: list[TargetVerdict]
