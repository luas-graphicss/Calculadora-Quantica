import io
import zipfile
from pathlib import Path

import pytest

from support.api import RUNS, read_run, signed_in_api, solved

_IMPORTS = "/api/v1/imports"
_COMPARISONS = "/api/v1/comparisons"
_NOTHING_DONE = "Nada foi importado nem calculado."


@pytest.fixture
def well(reference_cases: Path) -> bytes:
    return (reference_cases / "electron_box_1nm.json").read_bytes()


@pytest.fixture
def package(tmp_path: Path, well: bytes) -> bytes:
    with signed_in_api(tmp_path / "origin") as origin:
        identifier = solved(origin, well, "well-export-key")["run"]["identifier"]
        content: bytes = origin.get(f"{RUNS}/{identifier}/package").content
    return content


def _members(package: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _repacked(members: dict[str, bytes]) -> bytes:
    rebuilt = io.BytesIO()
    with zipfile.ZipFile(rebuilt, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return rebuilt.getvalue()


def test_a_finished_run_is_exported_as_a_package_named_after_it(
    tmp_path: Path, well: bytes
) -> None:
    with signed_in_api(tmp_path / "origin") as origin:
        identifier = solved(origin, well, "well-export-key")["run"]["identifier"]
        download = origin.get(f"{RUNS}/{identifier}/package")

    names = set(_members(download.content))
    assert download.headers["content-type"] == "application/zip"
    assert download.headers["content-disposition"] == (
        f'attachment; filename="qcalc-{identifier}.zip"'
    )
    assert {"manifest.json", "input.json", "problem.json", "outcome.json", "answers.csv"} <= names


def test_a_package_names_no_path_of_the_machine_that_wrote_it(
    tmp_path: Path, package: bytes
) -> None:
    members = _members(package)

    assert all(not name.startswith("/") and ".." not in name for name in members)
    assert all(str(tmp_path).encode() not in content for content in members.values())


def test_a_package_is_imported_into_an_empty_profile_without_calculating(
    tmp_path: Path, package: bytes, well: bytes
) -> None:
    with signed_in_api(tmp_path / "destination") as destination:
        imported = destination.post(_IMPORTS, content=package)
        repeated = destination.post(_IMPORTS, content=package)
        run = imported.json()["run"]
        details = read_run(destination, run["identifier"])
        history = destination.get(RUNS).json()["runs"]

    assert (imported.status_code, repeated.status_code) == (201, 200)
    assert repeated.json()["run"]["identifier"] == run["identifier"]
    assert (run["origin"], run["state"]) == ("imported", "succeeded")
    assert (run["verification_status"], run["headline"]) == ("passed", "E = 0.3760301621 eV")
    assert details["input"]["text"] == well.decode()
    assert details["outcome"]["result"]["value"]["decimal"] == "0.3760301621"
    assert [listed["identifier"] for listed in history] == [run["identifier"]]


def test_an_imported_run_is_rerun_on_request_and_agrees_with_the_package(
    tmp_path: Path, package: bytes
) -> None:
    with signed_in_api(tmp_path / "destination") as destination:
        imported = destination.post(_IMPORTS, content=package).json()["run"]
        source = read_run(destination, imported["identifier"])["input"]["text"].encode()
        rerun = solved(destination, source, "rerun-after-import", imported["identifier"])["run"]
        compared = {"base": imported["identifier"], "other": rerun["identifier"]}
        comparison = destination.get(_COMPARISONS, params=compared).json()

    (energy,) = comparison["answers"]
    assert (rerun["origin"], rerun["state"], rerun["verification_status"]) == (
        "local",
        "succeeded",
        "passed",
    )
    assert rerun["canonical_problem_sha256"] == imported["canonical_problem_sha256"]
    assert (energy["ratio"], comparison["input_differences"]) == ("1", [])
    assert comparison["version_divergences"] == []


@pytest.mark.parametrize("altered", ["outcome.json", "input.json", "problem.json"])
def test_a_package_with_an_altered_artifact_is_refused_before_anything_is_stored(
    tmp_path: Path, package: bytes, altered: str
) -> None:
    members = _members(package)
    tampered = _repacked({**members, altered: members[altered].replace(b"1", b"7", 1)})

    with signed_in_api(tmp_path / "destination") as destination:
        response = destination.post(_IMPORTS, content=tampered)
        history = destination.get(RUNS).json()["runs"]

    refusal = response.json()
    assert (response.status_code, refusal["code"]) == (422, "package_refused")
    assert refusal["message"].endswith(_NOTHING_DONE)
    assert history == []


def test_something_that_is_not_a_package_is_refused(tmp_path: Path) -> None:
    with signed_in_api(tmp_path / "destination") as destination:
        response = destination.post(_IMPORTS, content=b"not a reproduction package")
        history = destination.get(RUNS).json()["runs"]

    assert (response.status_code, response.json()["code"]) == (422, "package_refused")
    assert history == []
