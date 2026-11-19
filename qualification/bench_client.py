import html
import http.client
import re
import subprocess
import tempfile
from pathlib import Path
from types import TracebackType
from typing import Self
from urllib.parse import urlencode

API = "/api/v1"

_LOOPBACK = "127.0.0.1"
_LAUNCH_PAGE = "abrir-calculadora.html"
_ADDRESS = re.compile(r"http://127\.0\.0\.1:(\d+)")
_LAUNCH_CODE = re.compile(r'name="code" value="([^"]+)"')
_REQUEST_SECONDS = 300.0
_STOP_SECONDS = 30.0
_FIRST_ERROR_STATUS = 400


class BenchError(Exception):
    pass


class BenchClient:
    def __init__(self, command: str) -> None:
        self._data = tempfile.TemporaryDirectory(prefix="qcalc-bench-")
        self._server = subprocess.Popen(  # noqa: S603 - the command is the qcalc under qualification, with fixed arguments
            [command, "serve", "--no-browser", "--data-dir", self._data.name],
            stdout=subprocess.PIPE,
            text=True,
        )
        self._headers: dict[str, str] = {}
        self._connection: http.client.HTTPConnection | None = None

    @property
    def process(self) -> int:
        return self._server.pid

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

    def request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        if self._connection is None:
            raise BenchError("the bench session is not open")
        sent = {**self._headers, **(headers or {})}
        try:
            status, content = _answer(self._connection, method, path, body, sent)
        except ConnectionError:
            self._connection.close()
            status, content = _answer(self._connection, method, path, body, sent)
        if status >= _FIRST_ERROR_STATUS:
            raise BenchError(
                f"{method} {path} answered {status}: {content.decode('utf-8', 'replace')}"
            )
        return content

    def _open(self) -> None:
        if self._server.stdout is None:
            raise BenchError("the bench was started without a readable standard output")
        announcement = self._server.stdout.readline()
        address = _ADDRESS.search(announcement)
        if address is None:
            raise BenchError(f"the bench did not announce its address: {announcement!r}")
        port = int(address.group(1))
        launch_page = (Path(self._data.name) / _LAUNCH_PAGE).read_text("utf-8")
        code = _LAUNCH_CODE.search(launch_page)
        if code is None:
            raise BenchError("the launch page carries no access code")
        self._headers = {"Origin": f"http://{_LOOPBACK}:{port}"}
        self._connection = http.client.HTTPConnection(_LOOPBACK, port, timeout=_REQUEST_SECONDS)
        self._connection.request(
            "POST",
            f"{API}/session",
            urlencode({"code": html.unescape(code.group(1))}),
            {**self._headers, "Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self._connection.getresponse()
        response.read()
        cookie = response.getheader("Set-Cookie")
        if cookie is None:
            raise BenchError(f"the bench refused the session with status {response.status}")
        self._headers["Cookie"] = cookie.split(";", 1)[0]

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


def _answer(
    connection: http.client.HTTPConnection,
    method: str,
    path: str,
    body: bytes | None,
    headers: dict[str, str],
) -> tuple[int, bytes]:
    connection.request(method, path, body, headers)
    response = connection.getresponse()
    return response.status, response.read()
