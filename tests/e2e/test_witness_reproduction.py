import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from qualification.bench_client import BenchClient
from qualification.witness_packages import reproduce_package

_QCALC = str(Path(sys.executable).with_name("qcalc"))


@pytest.fixture(scope="module")
def benches() -> Iterator[tuple[BenchClient, BenchClient]]:
    with BenchClient(_QCALC) as bench, BenchClient(_QCALC) as receiver:
        yield bench, receiver


@pytest.fixture(scope="module")
def evidence(repository_root: Path) -> Path:
    return repository_root / "docs" / "evidence" / "phase-4"


def test_the_recorded_package_is_rerun_and_its_export_is_received_by_another_bench(
    benches: tuple[BenchClient, BenchClient], evidence: Path
) -> None:
    bench, receiver = benches

    reproduced = reproduce_package(bench, evidence / "electron_box_1nm.package.zip", receiver)

    assert reproduced["differences"] == []
    assert reproduced["imported_state"] == "succeeded"
    assert reproduced["rerun_state"] == "succeeded"
    assert reproduced["received_state"] == "succeeded"


def test_the_version_that_wrote_the_package_is_named_when_it_differs(
    benches: tuple[BenchClient, BenchClient], evidence: Path
) -> None:
    bench, receiver = benches

    reproduced = reproduce_package(bench, evidence / "electron_box_1nm.package.zip", receiver)

    assert "0.4.0" in [divergence["base"] for divergence in reproduced["version_divergences"]]


def test_an_altered_package_is_reported_without_being_rerun_or_handed_over(
    benches: tuple[BenchClient, BenchClient], evidence: Path
) -> None:
    bench, receiver = benches

    reproduced = reproduce_package(
        bench, evidence / "electron_box_1nm.altered_package.zip", receiver
    )

    assert reproduced["imported_state"] == "not imported"
    assert reproduced["rerun_state"] == "not rerun"
    assert reproduced["received_state"] == "not received"
    assert len(reproduced["differences"]) == 1
    assert "package_refused" in reproduced["differences"][0]
