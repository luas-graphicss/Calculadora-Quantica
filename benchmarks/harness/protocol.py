import json
from pathlib import Path
from typing import Literal, TypedDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

_PROFILE = "benchmarks/reference_profile.json"
_WORKLOADS = "benchmarks/workloads/index.json"


class MachineProfile(TypedDict):
    architecture: str
    logical_cpus: int
    memory_gibibytes: int
    operating_system: str
    python: str


class ExecutionProfile(TypedDict):
    concurrent_runs: int
    linear_algebra_threads: int
    result_cache: bool


class MeasurementProtocol(TypedDict):
    cold_runs: int
    warmup_runs: int
    measured_runs: int
    percentile_method: str


class Target(TypedDict):
    workload: str
    warm_p95_seconds: float
    worker_peak_rss_mebibytes: int


class ReferenceProfile(TypedDict):
    schema: str
    schema_version: str
    frozen_on: str
    machine: MachineProfile
    execution: ExecutionProfile
    protocol: MeasurementProtocol
    targets: list[Target]


class ExpectedAnswer(TypedDict):
    name: str
    expected: float
    tolerance: float
    comparison: Literal["absolute", "relative"]


class Workload(TypedDict):
    identifier: str
    title: str
    input: str
    oracle: str
    verification: str
    answers: list[ExpectedAnswer]


class RefusedRequest(TypedDict):
    identifier: str
    title: str
    input: str
    exit_code: int
    diagnostic: str


class WorkloadIndex(TypedDict):
    schema: str
    schema_version: str
    description: str
    workloads: list[Workload]
    refused_requests: list[RefusedRequest]


def load_profile(root: Path = REPOSITORY_ROOT) -> ReferenceProfile:
    profile: ReferenceProfile = json.loads((root / _PROFILE).read_text("utf-8"))
    return profile


def load_workloads(root: Path = REPOSITORY_ROOT) -> WorkloadIndex:
    index: WorkloadIndex = json.loads((root / _WORKLOADS).read_text("utf-8"))
    return index
