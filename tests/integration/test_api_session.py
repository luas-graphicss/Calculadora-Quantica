import stat
from collections.abc import Iterator
from pathlib import Path

import pytest

from quantum_calculator.interfaces.api.security.launch_page import write_launch_page
from support.api import ORIGIN, OpenedApi, opened_api, sign_in

_CATALOG = "/api/v1/catalog"
_SESSION = "/api/v1/session"
_UNKNOWN_RUN = "0" * 32
_LAUNCH_CODE = "launch-code-of-this-run"


@pytest.fixture
def api(tmp_path: Path) -> Iterator[OpenedApi]:
    with opened_api(tmp_path / "profile") as opened:
        yield opened


@pytest.mark.parametrize(
    "path",
    [
        _CATALOG,
        "/api/v1/runs",
        f"/api/v1/runs/{_UNKNOWN_RUN}",
        f"/api/v1/runs/{_UNKNOWN_RUN}/package",
        f"/api/v1/comparisons?base={_UNKNOWN_RUN}&other={_UNKNOWN_RUN}",
    ],
)
def test_research_data_is_refused_without_the_session_of_this_launch(
    api: OpenedApi, path: str
) -> None:
    response = api.client.get(path)

    assert response.status_code == 401
    assert response.json()["code"] == "session_required"


def test_nothing_is_calculated_or_imported_without_the_session(api: OpenedApi) -> None:
    submitted = api.client.post(
        "/api/v1/runs", content=b"{}", headers={"Idempotency-Key": "no-session-key"}
    )
    imported = api.client.post("/api/v1/imports", content=b"package")

    assert (submitted.status_code, imported.status_code) == (401, 401)


def test_a_wrong_launch_code_opens_no_session(api: OpenedApi) -> None:
    response = api.client.post(_SESSION, data={"code": "not-the-code-of-this-launch"})

    assert response.status_code == 403
    assert response.json()["code"] == "launch_code_refused"
    assert "set-cookie" not in response.headers
    assert api.client.get(_SESSION).status_code == 401


def test_the_launch_code_opens_a_session_kept_in_a_cookie_that_scripts_cannot_read(
    api: OpenedApi,
) -> None:
    response = api.client.post(_SESSION, data={"code": api.gate.launch_code})

    cookie = response.headers["set-cookie"]
    assert (response.status_code, response.headers["location"]) == (303, "/")
    assert {"HttpOnly", "SameSite=strict", "Path=/api/v1"} <= set(cookie.split("; "))
    assert api.gate.launch_code not in cookie
    assert api.client.get(_SESSION).status_code == 204
    assert api.client.get(_CATALOG).status_code == 200


def test_the_launch_code_is_not_accepted_as_a_session(api: OpenedApi) -> None:
    api.client.cookies.set("qcalc_session", api.gate.launch_code)

    assert api.client.get(_CATALOG).status_code == 401


def test_a_request_addressed_to_another_host_is_refused(api: OpenedApi) -> None:
    sign_in(api)

    response = api.client.get(_CATALOG, headers={"Host": "calculadora.example"})

    assert (response.status_code, response.json()["code"]) == (421, "host_not_allowed")


@pytest.mark.parametrize(
    "origin",
    ["http://calculadora.example", "null", "http://127.0.0.1:9", "https://127.0.0.1:8421"],
)
def test_a_request_from_another_page_is_refused_even_with_the_session(
    api: OpenedApi, origin: str
) -> None:
    sign_in(api)

    response = api.client.get(_CATALOG, headers={"Origin": origin})

    assert (response.status_code, response.json()["code"]) == (403, "origin_not_allowed")


def test_the_interface_served_by_the_bench_is_an_accepted_origin(api: OpenedApi) -> None:
    sign_in(api)

    assert api.client.get(_CATALOG, headers={"Origin": ORIGIN}).status_code == 200


def test_the_launch_page_opened_from_a_file_may_post_the_code(api: OpenedApi) -> None:
    response = api.client.post(
        _SESSION, data={"code": api.gate.launch_code}, headers={"Origin": "null"}
    )

    assert response.status_code == 303


def test_responses_forbid_framing_sniffing_and_caching_of_research_data(api: OpenedApi) -> None:
    sign_in(api)

    headers = api.client.get(_CATALOG).headers

    policy = headers["content-security-policy"].split("; ")
    assert headers["cache-control"] == "no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert {"default-src 'self'", "script-src 'self'", "connect-src 'self'"} <= set(policy)
    assert {"frame-ancestors 'none'", "object-src 'none'"} <= set(policy)


def test_without_a_built_interface_the_root_says_so_in_plain_text(api: OpenedApi) -> None:
    response = api.client.get("/")

    assert response.status_code == 200
    assert response.text.startswith("A interface web não acompanha esta instalação")


def test_a_built_interface_is_served_at_the_root_without_a_session(tmp_path: Path) -> None:
    interface = tmp_path / "interface"
    interface.mkdir()
    (interface / "index.html").write_text("<!doctype html><title>Bancada</title>", "utf-8")

    with opened_api(tmp_path / "profile", interface) as opened:
        page = opened.client.get("/")
        data = opened.client.get(_CATALOG)

    assert (page.status_code, page.text) == (200, "<!doctype html><title>Bancada</title>")
    assert "cache-control" not in page.headers
    assert data.status_code == 401


def test_the_launch_page_is_private_and_posts_the_code_outside_the_address(
    tmp_path: Path,
) -> None:
    page = write_launch_page(tmp_path, 8421, _LAUNCH_CODE)

    content = page.read_text("utf-8")
    assert stat.S_IMODE(page.stat().st_mode) == 0o600
    assert '<form method="post" action="http://127.0.0.1:8421/api/v1/session">' in content
    assert f'<input type="hidden" name="code" value="{_LAUNCH_CODE}">' in content
    assert content.count(_LAUNCH_CODE) == 1


def test_a_launch_page_left_by_an_earlier_launch_is_replaced(tmp_path: Path) -> None:
    write_launch_page(tmp_path, 8421, "code-of-the-earlier-launch")

    page = write_launch_page(tmp_path, 8422, _LAUNCH_CODE)

    content = page.read_text("utf-8")
    assert "code-of-the-earlier-launch" not in content
    assert "http://127.0.0.1:8422/api/v1/session" in content
