import os
import re
import signal
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest

from support.processes import session_is_empty, wait_until
from support.sessions import LONG_CALCULATION, TIME_LIMIT

_LAUNCH_CODE = re.compile(r'name="code" value="([^"]+)"')
_ADDRESS_PREFIX = "Bancada em "
_PAGE_PREFIX = "Arquivo de acesso: "
_INTERFACE = "<!doctype html><title>Bancada de teste</title>"
_RUNS = "/api/v1/runs"
_ACTIVE_STATES = {"queued", "running"}


@dataclass(frozen=True, slots=True)
class RunningBench:
    process: subprocess.Popen[str]
    url: str
    launch_page: Path

    @contextmanager
    def session(self) -> Iterator[httpx.Client]:
        code = _LAUNCH_CODE.search(self.launch_page.read_text("utf-8"))
        assert code is not None
        with httpx.Client(base_url=self.url, timeout=30.0) as client:
            opened = client.post("/api/v1/session", data={"code": code.group(1)})
            assert opened.status_code == 303
            yield client


@contextmanager
def _bench(profile: Path, interface: Path) -> Iterator[RunningBench]:
    command = [sys.executable, "-m", "quantum_calculator", "serve", "--no-browser"]
    process = subprocess.Popen(
        [*command, "--data-dir", str(profile), "--web-root", str(interface)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        start_new_session=True,
    )
    try:
        assert process.stdout is not None
        address = process.stdout.readline().strip()
        page = process.stdout.readline().strip()
        assert address.startswith(_ADDRESS_PREFIX), process.stderr and process.stderr.read()
        assert page.startswith(_PAGE_PREFIX)
        yield RunningBench(
            process, address.removeprefix(_ADDRESS_PREFIX), Path(page.removeprefix(_PAGE_PREFIX))
        )
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate(timeout=60)


@pytest.fixture
def interface(tmp_path: Path) -> Path:
    directory = tmp_path / "interface"
    directory.mkdir()
    (directory / "index.html").write_text(_INTERFACE, "utf-8")
    return directory


def _run(client: httpx.Client, identifier: str) -> dict[str, Any]:
    details: dict[str, Any] = client.get(f"{_RUNS}/{identifier}").json()
    return details


def _submit(client: httpx.Client, source: bytes, key: str) -> str:
    response = client.post(
        _RUNS,
        content=source,
        headers={"Idempotency-Key": key},
        params={"time_limit": TIME_LIMIT},
    )
    assert response.status_code == 202, response.text
    identifier: str = response.json()["run"]["identifier"]
    return identifier


@pytest.mark.parametrize("stop", [signal.SIGINT, signal.SIGTERM])
def test_the_bench_serves_the_interface_and_gives_data_only_to_the_launch_session(
    tmp_path: Path, interface: Path, stop: signal.Signals
) -> None:
    with _bench(tmp_path / "profile", interface) as bench:
        page = httpx.get(f"{bench.url}/")
        refused = httpx.get(f"{bench.url}/api/v1/catalog")
        with bench.session() as client:
            catalog = client.get("/api/v1/catalog")
        os.killpg(bench.process.pid, stop)
        bench.process.wait(timeout=60)

    assert (page.status_code, page.text) == (200, _INTERFACE)
    assert refused.status_code == 401
    assert catalog.status_code == 200
    assert catalog.json()["document"] == "workbench_catalog"
    assert bench.process.returncode == 0
    assert not bench.launch_page.exists()
    wait_until(lambda: session_is_empty(bench.process.pid))


def test_killing_the_bench_during_a_calculation_shows_no_result_after_the_restart(
    tmp_path: Path, interface: Path, reference_cases: Path
) -> None:
    profile = tmp_path / "profile"
    well = (reference_cases / "electron_box_1nm.json").read_bytes()
    with _bench(profile, interface) as bench, bench.session() as client:
        finished = _submit(client, well, "bench-well-key")
        wait_until(lambda: _run(client, finished)["run"]["state"] not in _ACTIVE_STATES, 120)
        unfinished = _submit(client, LONG_CALCULATION, "bench-long-key")
        wait_until(lambda: _run(client, unfinished)["run"]["state"] == "running")
        os.killpg(bench.process.pid, signal.SIGKILL)
        bench.process.wait(timeout=60)
    wait_until(lambda: session_is_empty(bench.process.pid))

    with _bench(profile, interface) as restarted, restarted.session() as client:
        interrupted = _run(client, unfinished)
        kept = _run(client, finished)
        listed = [run["identifier"] for run in client.get(_RUNS).json()["runs"]]
        os.killpg(restarted.process.pid, signal.SIGINT)
        restarted.process.wait(timeout=60)

    assert interrupted["run"]["state"] == "interrupted"
    assert (interrupted["run"]["verification_status"], interrupted["run"]["headline"]) == (
        None,
        None,
    )
    assert interrupted["outcome"] is None
    assert (kept["run"]["state"], kept["run"]["headline"]) == ("succeeded", "E = 0.3760301621 eV")
    assert kept["outcome"]["verification"]["status"] == "passed"
    assert listed == [unfinished, finished]
    assert restarted.process.returncode == 0
