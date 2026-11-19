from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from quantum_calculator.interfaces.api.application import ApiSettings, create_api
from quantum_calculator.interfaces.api.documents import API_PREFIX, SESSION_PATH
from quantum_calculator.interfaces.api.security.session import SessionGate
from quantum_calculator.workbench_composition import build_workbench
from support.processes import wait_until

PORT = 8421
ORIGIN = f"http://127.0.0.1:{PORT}"
RUNS = f"{API_PREFIX}/runs"

type Json = dict[str, Any]

_SEE_OTHER = 303
_ACCEPTED_OR_REPLAYED = (200, 202)
_ACTIVE_STATES = frozenset({"queued", "running"})
_SETTLE_SECONDS = 120.0


@dataclass(frozen=True, slots=True)
class OpenedApi:
    client: TestClient
    gate: SessionGate


@contextmanager
def opened_api(directory: Path, web_root: Path | None = None) -> Iterator[OpenedApi]:
    gate = SessionGate()
    api = create_api(build_workbench(directory), gate, ApiSettings(PORT, web_root))
    with TestClient(api, base_url=ORIGIN, follow_redirects=False) as client:
        yield OpenedApi(client, gate)


@contextmanager
def signed_in_api(directory: Path) -> Iterator[TestClient]:
    with opened_api(directory) as opened:
        sign_in(opened)
        yield opened.client


def sign_in(opened: OpenedApi) -> None:
    response = opened.client.post(SESSION_PATH, data={"code": opened.gate.launch_code})
    assert response.status_code == _SEE_OTHER


def submit(
    client: TestClient,
    source: bytes,
    key: str,
    parent: str | None = None,
    time_limit: float | None = None,
) -> Json:
    parameters: dict[str, str | float] = {}
    if parent is not None:
        parameters["parent"] = parent
    if time_limit is not None:
        parameters["time_limit"] = time_limit
    response = client.post(
        RUNS, content=source, headers={"Idempotency-Key": key}, params=parameters
    )
    assert response.status_code in _ACCEPTED_OR_REPLAYED, response.text
    run: Json = response.json()["run"]
    return run


def read_run(client: TestClient, identifier: str) -> Json:
    details: Json = client.get(f"{RUNS}/{identifier}").json()
    return details


def settled(client: TestClient, identifier: str) -> Json:
    wait_until(
        lambda: read_run(client, identifier)["run"]["state"] not in _ACTIVE_STATES,
        _SETTLE_SECONDS,
    )
    return read_run(client, identifier)


def solved(client: TestClient, source: bytes, key: str, parent: str | None = None) -> Json:
    return settled(client, submit(client, source, key, parent)["identifier"])
