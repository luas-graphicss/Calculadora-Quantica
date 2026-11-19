from benchmarks.harness.protocol import Target
from benchmarks.harness.report import TimedRuns, WorkloadMeasurement
from benchmarks.harness.statistics import summarize
from benchmarks.harness.targets import evaluate_targets

MEBIBYTE = 1024**2
TARGET = Target(workload="well", warm_p95_seconds=2.0, worker_peak_rss_mebibytes=512)


def timed(seconds: list[float]) -> TimedRuns:
    return TimedRuns(runs_seconds=seconds, summary=summarize(seconds))


def measured(warm_seconds: list[float], bench_peak: int, staged_peak: int) -> WorkloadMeasurement:
    return WorkloadMeasurement(
        identifier="well",
        title="well",
        input="benchmarks/workloads/well.json",
        cold=timed([1.0]),
        warm={
            "runs_seconds": warm_seconds,
            "summary": summarize(warm_seconds),
            "worker_peak_rss_bytes": bench_peak,
        },
        staged={"stages": {}, "total": timed([0.5]), "worker_peak_rss_bytes": staged_peak},
        precision={"checked_records": 1, "verification": "passed", "answers": []},
    )


def test_target_is_met_when_the_warm_p95_and_the_worker_peak_stay_within_the_limits() -> None:
    (verdict,) = evaluate_targets(
        [TARGET], [measured([0.8, 0.9, 1.9], 120 * MEBIBYTE, 110 * MEBIBYTE)]
    )

    assert verdict["met"]
    assert verdict["warm_p95_seconds"] == 1.9
    assert verdict["worker_peak_rss_mebibytes"] == 120.0


def test_target_is_missed_when_the_warm_p95_passes_the_limit() -> None:
    (verdict,) = evaluate_targets([TARGET], [measured([0.8, 2.1], MEBIBYTE, MEBIBYTE)])

    assert not verdict["met"]


def test_target_counts_the_larger_of_the_two_worker_peaks() -> None:
    (verdict,) = evaluate_targets([TARGET], [measured([0.8], 100 * MEBIBYTE, 600 * MEBIBYTE)])

    assert not verdict["met"]
    assert verdict["worker_peak_rss_mebibytes"] == 600.0
