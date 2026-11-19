import json
import time
import uuid
from dataclasses import dataclass
from types import TracebackType
from typing import NotRequired, Self, TypedDict

from benchmarks.harness.precision import NumericalRecord
from benchmarks.harness.worker_memory import require_children_listing, worker_peak_rss_bytes
from qualification.bench_client import API, BenchClient, BenchError

_ACTIVE_STATES = frozenset({"queued", "running"})
_SUCCEEDED = "succeeded"
_POLL_SECONDS = 0.005


class _Run(TypedDict):
    identifier: str
    state: str


class _RunDocument(TypedDict):
    run: _Run
    outcome: NotRequired[NumericalRecord | None]


@dataclass(frozen=True, slots=True)
class BenchRun:
    seconds: float
    record: NumericalRecord
    worker_peak_rss_bytes: int


class BenchSession:
    def __init__(self, command: str) -> None:
        self._client = BenchClient(command)

    def __enter__(self) -> Self:
        self._client.__enter__()
        try:
            require_children_listing(self._client.process)
        except BaseException:
            self._client.__exit__(None, None, None)
            raise
        return self

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._client.__exit__(error_type, error, traceback)

    def calculate(self, source: bytes) -> BenchRun:
        started = time.perf_counter()
        submitted = self._exchange(
            "POST",
            f"{API}/runs",
            source,
            {"Idempotency-Key": uuid.uuid4().hex, "Content-Type": "application/json"},
        )
        path = f"{API}/runs/{submitted['run']['identifier']}"
        peak = 0
        while (details := self._exchange("GET", path))["run"]["state"] in _ACTIVE_STATES:
            peak = max(peak, worker_peak_rss_bytes(self._client.process))
            time.sleep(_POLL_SECONDS)
        seconds = time.perf_counter() - started
        outcome = details.get("outcome")
        if details["run"]["state"] != _SUCCEEDED or outcome is None:
            raise BenchError(f"the bench ended the run as {details['run']['state']}")
        return BenchRun(seconds, outcome, peak)

    def _exchange(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> _RunDocument:
        document: _RunDocument = json.loads(self._client.request(method, path, body, headers))
        return document
