import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import TypedDict

from qualification.bench_client import API, BenchClient, BenchError
from qualification.documents import ReproducedPackage, VersionDivergence

_ACTIVE_STATES = frozenset({"queued", "running"})
_SUCCEEDED = "succeeded"
_NOT_IMPORTED = "not imported"
_NOT_RERUN = "not rerun"
_POLL_SECONDS = 0.05
_RATIO_TOLERANCE = 1e-9


class _Run(TypedDict):
    identifier: str
    state: str


class _RunDocument(TypedDict):
    run: _Run


class _InputText(TypedDict):
    text: str


class _RunDetails(TypedDict):
    run: _Run
    input: _InputText


class _InputDifference(TypedDict):
    pointer: str


class _ComparedAnswer(TypedDict):
    name: str
    ratio: str | float | None


class _Comparison(TypedDict):
    version_divergences: list[VersionDivergence]
    input_differences: list[_InputDifference]
    answers: list[_ComparedAnswer]


def reproduce_package(bench: BenchClient, package: Path) -> ReproducedPackage:
    content = package.read_bytes()
    reproduced = ReproducedPackage(
        package=package.name,
        sha256=hashlib.sha256(content).hexdigest(),
        imported_state=_NOT_IMPORTED,
        rerun_state=_NOT_RERUN,
        version_divergences=[],
        differences=[],
    )
    try:
        _import_and_rerun(bench, content, reproduced)
    except BenchError as refusal:
        reproduced["differences"].append(str(refusal))
    return reproduced


def _import_and_rerun(bench: BenchClient, content: bytes, reproduced: ReproducedPackage) -> None:
    imported: _RunDocument = json.loads(
        bench.request("POST", f"{API}/imports", content, {"Content-Type": "application/zip"})
    )
    base = imported["run"]["identifier"]
    reproduced["imported_state"] = imported["run"]["state"]
    details: _RunDetails = json.loads(bench.request("GET", f"{API}/runs/{base}"))
    submitted: _RunDocument = json.loads(
        bench.request(
            "POST",
            f"{API}/runs?parent={base}",
            details["input"]["text"].encode("utf-8"),
            {"Idempotency-Key": uuid.uuid4().hex, "Content-Type": "application/json"},
        )
    )
    other = submitted["run"]["identifier"]
    reproduced["rerun_state"] = _settled_state(bench, other)
    if reproduced["rerun_state"] != _SUCCEEDED:
        reproduced["differences"].append(f"the rerun ended as {reproduced['rerun_state']}")
        return
    comparison: _Comparison = json.loads(
        bench.request("GET", f"{API}/comparisons?base={base}&other={other}")
    )
    reproduced["version_divergences"] = comparison["version_divergences"]
    reproduced["differences"] += [
        f"the rerun read another input at {difference['pointer']}"
        for difference in comparison["input_differences"]
    ]
    reproduced["differences"] += [
        f"{answer['name']} has ratio {answer['ratio']} to the packaged answer"
        for answer in comparison["answers"]
        if answer["ratio"] is None or abs(float(answer["ratio"]) - 1) > _RATIO_TOLERANCE
    ]


def _settled_state(bench: BenchClient, identifier: str) -> str:
    while True:
        document: _RunDocument = json.loads(bench.request("GET", f"{API}/runs/{identifier}"))
        if document["run"]["state"] not in _ACTIVE_STATES:
            return document["run"]["state"]
        time.sleep(_POLL_SECONDS)
