from collections.abc import Sequence

from benchmarks.harness.protocol import Target
from benchmarks.harness.report import TargetVerdict, WorkloadMeasurement

_MEBIBYTE = 1024**2


def evaluate_targets(
    targets: Sequence[Target], workloads: Sequence[WorkloadMeasurement]
) -> list[TargetVerdict]:
    measured = {workload["identifier"]: workload for workload in workloads}
    return [_verdict(target, measured[target["workload"]]) for target in targets]


def _verdict(target: Target, workload: WorkloadMeasurement) -> TargetVerdict:
    warm_p95 = workload["warm"]["summary"]["p95"]
    peak_bytes = max(
        workload["warm"]["worker_peak_rss_bytes"], workload["staged"]["worker_peak_rss_bytes"]
    )
    peak = peak_bytes / _MEBIBYTE
    return TargetVerdict(
        workload=target["workload"],
        warm_p95_seconds=warm_p95,
        warm_p95_limit_seconds=target["warm_p95_seconds"],
        worker_peak_rss_mebibytes=peak,
        worker_peak_rss_limit_mebibytes=target["worker_peak_rss_mebibytes"],
        met=warm_p95 <= target["warm_p95_seconds"] and peak <= target["worker_peak_rss_mebibytes"],
    )
