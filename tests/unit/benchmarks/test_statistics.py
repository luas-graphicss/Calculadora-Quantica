import pytest

from benchmarks.harness.statistics import percentile, summarize


def test_percentile_uses_the_nearest_rank_of_thirty_measured_runs() -> None:
    seconds = [float(run) for run in range(1, 31)]

    assert percentile(seconds, 50) == 15.0
    assert percentile(seconds, 95) == 29.0


def test_percentile_of_a_single_run_is_that_run() -> None:
    assert percentile([0.75], 95) == 0.75


def test_percentile_does_not_depend_on_the_order_of_the_runs() -> None:
    assert percentile([3.0, 1.0, 2.0], 50) == 2.0


def test_summary_reports_the_extremes_and_the_mean() -> None:
    summary = summarize([0.2, 0.4, 0.9])

    assert summary["count"] == 3
    assert summary["minimum"] == 0.2
    assert summary["maximum"] == 0.9
    assert summary["mean"] == pytest.approx(0.5)
