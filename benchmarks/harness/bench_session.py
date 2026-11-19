import html
import http.client
import json
import re
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import NotRequired, Self, TypedDict
from urllib.parse import urlencode

from benchmarks.harness.precision import NumericalRecord
from benchmarks.harness.worker_memory import require_children_listing, worker_peak_rss_bytes

_API = "/api/v1"
_LOOPBACK = "127.0.0.1"
_LAUNCH_PAGE = "abrir-calculadora.html"
_ADDRESS = re.compile(r"http://127\.0\.0\.1:(\d+)")
_LAUNCH_CODE = re.compile(r'name="code" value="([^"]+)"')
_ACTIVE_STATES = frozenset({"queued", "running"})
_SUCCEEDED = "succeeded"
_POLL_SECONDS = 0.005
_REQUEST_SECONDS = 300.0
_STOP_SECONDS = 30.0
_FIRST_ERROR_STATUS = 400


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


class BenchError(Exception):
    pass


class BenchSession:
    def __init__(self, command: str) -> None:
        self._data = tempfile.TemporaryDirectory(prefix="qcalc-benchmark-")
        self._server = subprocess.Popen(  # noqa: S603 - the command is the qcalc under measurement, with fixed arguments
            [command, "serve", "--no-browser", "--data-dir", self._data.name],
            stdout=subprocess.PIPE,
            text=True,
        )
        self._headers: dict[str, str] = {}
        self._connection: http.client.HTTPConnection | None = None

    def __enter__(self) -> Self:
        try:
            self._open()
        except BaseException:
            self._stop()
            raise
        return self

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._stop()

    def calculate(self, source: bytes) -> BenchRun:
        started = time.perf_counter()
        submitted = self._exchange(
            "POST",
            f"{_API}/runs",
            source,
            {"Idempotency-Key": uuid.uuid4().hex, "Content-Type": "application/json"},
        )
        path = f"{_API}/runs/{submitted['run']['identifier']}"
        peak = 0
        while (details := self._exchange("GET", path))["run"]["state"] in _ACTIVE_STATES:
            peak = max(peak, worker_peak_rss_bytes(self._server.pid))
            time.sleep(_POLL_SECONDS)
        seconds = time.perf_counter() - started
        outcome = details.get("outcome")
        if details["run"]["state"] != _SUCCEEDED or outcome is None:
            raise BenchError(f"the bench ended the run as {details['run']['state']}")
        return BenchRun(seconds, outcome, peak)

    def _open(self) -> None:
        if self._server.stdout is None:
            raise BenchError("the bench was started without a readable standard output")
        announcement = self._server.stdout.readline()
        address = _ADDRESS.search(announcement)
        if address is None:
            raise BenchError(f"the bench did not announce its address: {announcement!r}")
        require_children_listing(self._server.pid)
        port = int(address.group(1))
        launch_page = (Path(self._data.name) / _LAUNCH_PAGE).read_text("utf-8")
        code = _LAUNCH_CODE.search(launch_page)
        if code is None:
            raise BenchError("the launch page carries no access code")
        self._headers = {"Origin": f"http://{_LOOPBACK}:{port}"}
        self._connection = http.client.HTTPConnection(_LOOPBACK, port, timeout=_REQUEST_SECONDS)
        self._connection.request(
            "POST",
            f"{_API}/session",
            urlencode({"code": html.unescape(code.group(1))}),
            {**self._headers, "Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self._connection.getresponse()
        response.read()
        cookie = response.getheader("Set-Cookie")
        if cookie is None:
            raise BenchError(f"the bench refused the session with status {response.status}")
        self._headers["Cookie"] = cookie.split(";", 1)[0]

    def _exchange(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> _RunDocument:
        if self._connection is None:
            raise BenchError("the bench session is not open")
        self._connection.request(method, path, body, {**self._headers, **(headers or {})})
        response = self._connection.getresponse()
        content = response.read()
        if response.status >= _FIRST_ERROR_STATUS:
            raise BenchError(
                f"{method} {path} answered {response.status}: {content.decode('utf-8', 'replace')}"
            )
        document: _RunDocument = json.loads(content)
        return document

    def _stop(self) -> None:
        if self._connection is not None:
            self._connection.close()
        self._server.terminate()
        try:
            self._server.wait(_STOP_SECONDS)
        except subprocess.TimeoutExpired:
            self._server.kill()
            self._server.wait()
        if self._server.stdout is not None:
            self._server.stdout.close()
        self._data.cleanup()
