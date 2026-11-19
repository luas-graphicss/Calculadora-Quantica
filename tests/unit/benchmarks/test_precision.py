import pytest

from benchmarks.harness.precision import NumericalRecord, PrecisionError, PrecisionLedger
from benchmarks.harness.protocol import Workload

WORKLOAD = Workload(
    identifier="two_levels",
    title="two levels",
    input="benchmarks/workloads/two_levels.json",
    oracle="E_2 = 4 E_1",
    verification="passed",
    answers=[
        {"name": "energy_1", "expected": 2.0, "tolerance": 1e-3, "comparison": "relative"},
        {"name": "drift", "expected": 0.0, "tolerance": 1e-9, "comparison": "absolute"},
    ],
)


def record(energy: float, drift: float, status: str = "passed") -> NumericalRecord:
    return {
        "result": {
            "answers": [{"name": "energy_1", "value": energy}, {"name": "drift", "value": drift}]
        },
        "verification": {"status": status},
    }


def test_ledger_keeps_the_largest_deviation_of_each_answer() -> None:
    ledger = PrecisionLedger(WORKLOAD)

    ledger.check(record(2.001, 2e-10))
    ledger.check(record(1.9995, -5e-10))

    report = ledger.report()
    assert report["checked_records"] == 2
    energy, drift = report["answers"]
    assert energy["largest_deviation"] == pytest.approx(5e-4)
    assert drift["largest_deviation"] == pytest.approx(5e-10)


def test_ledger_refuses_a_measurement_that_lost_precision() -> None:
    with pytest.raises(PrecisionError, match="energy_1"):
        PrecisionLedger(WORKLOAD).check(record(2.01, 0.0))


def test_ledger_refuses_a_value_that_is_not_a_number() -> None:
    with pytest.raises(PrecisionError, match="drift"):
        PrecisionLedger(WORKLOAD).check(record(2.0, float("nan")))


def test_ledger_refuses_a_verification_verdict_other_than_the_expected_one() -> None:
    with pytest.raises(PrecisionError, match="inconclusive"):
        PrecisionLedger(WORKLOAD).check(record(2.0, 0.0, status="inconclusive"))
