import json
import shutil
import sys
from pathlib import Path

import pytest

from benchmarks.harness.baseline import render_comparison
from benchmarks.harness.environment import THREAD_VARIABLES
from benchmarks.harness.measurement import measure
from benchmarks.harness.protocol import load_profile, load_workloads
from benchmarks.harness.stages import STAGES
from benchmarks.harness.summary import render_summary

QCALC = Path(sys.executable).with_name("qcalc")
SHORT_PROTOCOL = {"cold_runs": 1, "warmup_runs": 1, "measured_runs": 2}
MEASURED = "decay_trajectory"

pytestmark = pytest.mark.skipif(not QCALC.exists(), reason="the qcalc command is not installed")


@pytest.fixture(scope="module")
def short_benchmark(tmp_path_factory: pytest.TempPathFactory, repository_root: Path) -> Path:
    root = tmp_path_factory.mktemp("benchmark")
    profile = load_profile()
    profile["protocol"].update(SHORT_PROTOCOL)  # type: ignore[typeddict-item]  # a shorter protocol with the same keys
    profile["targets"] = [
        {"workload": MEASURED, "warm_p95_seconds": 60.0, "worker_peak_rss_mebibytes": 512}
    ]
    index = load_workloads()
    index["workloads"] = [
        workload for workload in index["workloads"] if workload["identifier"] == MEASURED
    ]
    (root / "benchmarks" / "workloads").mkdir(parents=True)
    (root / "benchmarks" / "reference_profile.json").write_text(json.dumps(profile), "utf-8")
    (root / "benchmarks" / "workloads" / "index.json").write_text(json.dumps(index), "utf-8")
    shutil.copytree(repository_root / "reference_cases", root / "reference_cases")
    return root


def test_measurement_times_the_cold_warm_and_staged_paths_and_checks_each_answer(
    short_benchmark: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for variable in THREAD_VARIABLES:
        monkeypatch.setenv(variable, "unpinned")

    report = measure(short_benchmark, str(QCALC), lambda _workload: None)

    (workload,) = report["workloads"]
    assert workload["identifier"] == MEASURED
    assert len(workload["cold"]["runs_seconds"]) == 1
    assert len(workload["warm"]["runs_seconds"]) == 2
    assert tuple(workload["staged"]["stages"]) == STAGES
    assert all(len(timed["runs_seconds"]) == 2 for timed in workload["staged"]["stages"].values())
    assert workload["warm"]["worker_peak_rss_bytes"] > 0
    assert workload["staged"]["worker_peak_rss_bytes"] > 0
    assert workload["precision"]["checked_records"] == 7
    assert workload["precision"]["answers"][0]["largest_deviation"] <= 1e-8

    (refusal,) = report["refused_requests"]
    assert refusal["exit_code"] == 7
    assert [diagnostic["code"] for diagnostic in refusal["diagnostics"]] == [
        "resource_limit_exceeded"
    ]

    (verdict,) = report["targets"]
    assert verdict["met"]
    assert report["machine"]["linear_algebra_threads"] == dict.fromkeys(THREAD_VARIABLES, "1")

    summary = render_summary(report)
    assert "decaimento exponencial" in summary
    assert "resource_limit_exceeded" in summary
    assert "atingida nesta máquina" in summary
    assert "mesma CPU" in render_comparison(report, report)
