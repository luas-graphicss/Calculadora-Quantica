from typing import TypedDict

from benchmarks.harness.protocol import ExpectedAnswer, Workload


class RecordedAnswer(TypedDict):
    name: str
    value: float


class RecordedResult(TypedDict):
    answers: list[RecordedAnswer]


class RecordedVerification(TypedDict):
    status: str


class NumericalRecord(TypedDict):
    result: RecordedResult
    verification: RecordedVerification


class LargestDeviation(TypedDict):
    name: str
    expected: float
    tolerance: float
    comparison: str
    largest_deviation: float


class PrecisionReport(TypedDict):
    checked_records: int
    verification: str
    answers: list[LargestDeviation]


class PrecisionError(Exception):
    pass


class PrecisionLedger:
    def __init__(self, workload: Workload) -> None:
        self._workload = workload
        self._checked = 0
        self._largest = {answer["name"]: 0.0 for answer in workload["answers"]}

    def check(self, record: NumericalRecord) -> None:
        workload = self._workload
        status = record["verification"]["status"]
        if status != workload["verification"]:
            raise PrecisionError(
                f"workload {workload['identifier']} ended with verification {status!r}, "
                f"expected {workload['verification']!r}"
            )
        observed = {answer["name"]: answer["value"] for answer in record["result"]["answers"]}
        for expected in workload["answers"]:
            deviation = _deviation(expected, observed[expected["name"]])
            if not deviation <= expected["tolerance"]:
                raise PrecisionError(
                    f"workload {workload['identifier']} answered {expected['name']} = "
                    f"{observed[expected['name']]!r}, a {expected['comparison']} deviation of "
                    f"{deviation:.3e} from {expected['expected']!r}, above "
                    f"{expected['tolerance']:.3e}"
                )
            self._largest[expected["name"]] = max(self._largest[expected["name"]], deviation)
        self._checked += 1

    def report(self) -> PrecisionReport:
        return PrecisionReport(
            checked_records=self._checked,
            verification=self._workload["verification"],
            answers=[
                LargestDeviation(
                    name=answer["name"],
                    expected=answer["expected"],
                    tolerance=answer["tolerance"],
                    comparison=answer["comparison"],
                    largest_deviation=self._largest[answer["name"]],
                )
                for answer in self._workload["answers"]
            ],
        )


def _deviation(expected: ExpectedAnswer, observed: float) -> float:
    difference = abs(observed - expected["expected"])
    if expected["comparison"] == "relative":
        return difference / abs(expected["expected"])
    return difference
