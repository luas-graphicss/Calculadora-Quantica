from pathlib import Path

from benchmarks.harness.protocol import load_profile, load_workloads


def test_frozen_profile_keeps_the_machine_and_the_protocol_of_the_roadmap() -> None:
    profile = load_profile()

    assert profile["machine"] == {
        "architecture": "x86_64",
        "logical_cpus": 4,
        "memory_gibibytes": 8,
        "operating_system": "Ubuntu 24.04",
        "python": "CPython 3.12",
    }
    assert profile["execution"] == {
        "concurrent_runs": 1,
        "linear_algebra_threads": 1,
        "result_cache": False,
    }
    assert profile["protocol"]["warmup_runs"] == 5
    assert profile["protocol"]["measured_runs"] == 30


def test_performance_target_is_the_six_level_well_within_two_seconds_and_512_mebibytes(
    repository_root: Path,
) -> None:
    (target,) = load_profile()["targets"]
    workloads = {workload["identifier"]: workload for workload in load_workloads()["workloads"]}

    assert target == {
        "workload": "well_six_levels_4096",
        "warm_p95_seconds": 2.0,
        "worker_peak_rss_mebibytes": 512,
    }
    source = (repository_root / workloads[target["workload"]]["input"]).read_text("utf-8")
    assert '"subintervals": 4096' in source
    assert '"levels": 6' in source


def test_every_workload_has_an_input_and_an_oracle_with_a_tolerance(
    repository_root: Path,
) -> None:
    index = load_workloads()

    assert [workload["identifier"] for workload in index["workloads"]] == [
        "well_six_levels_4096",
        "oscillator_six_levels_4096",
        "decay_trajectory",
        "well_beat_evolution",
    ]
    for workload in index["workloads"]:
        assert (repository_root / workload["input"]).is_file()
        assert workload["oracle"]
        assert workload["answers"]
        assert all(answer["tolerance"] > 0 for answer in workload["answers"])


def test_a_request_above_the_profile_is_part_of_the_measurement(repository_root: Path) -> None:
    (request,) = load_workloads()["refused_requests"]

    assert (repository_root / request["input"]).is_file()
    assert request["exit_code"] == 7
    assert request["diagnostic"] == "resource_limit_exceeded"
