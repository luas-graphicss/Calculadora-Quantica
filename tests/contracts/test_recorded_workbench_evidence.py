import io
import zipfile
from pathlib import Path

import pytest

from support.api import RUNS, read_run, signed_in_api, solved

_IMPORTS = "/api/v1/imports"
_COMPARISONS = "/api/v1/comparisons"
_RECORDED_ENERGY = "E = 0.3760301621 eV"
_ALTERED_ARTIFACT = "o arquivo answers.csv não confere com o hash declarado no manifesto"


@pytest.fixture(scope="module")
def evidence(repository_root: Path) -> Path:
    return repository_root / "docs" / "evidence" / "phase-4"


@pytest.fixture(scope="module")
def recorded_package(evidence: Path) -> bytes:
    return (evidence / "electron_box_1nm.package.zip").read_bytes()


def test_recorded_package_is_still_imported_without_calculating(
    tmp_path: Path, recorded_package: bytes
) -> None:
    with signed_in_api(tmp_path) as bench:
        imported = bench.post(_IMPORTS, content=recorded_package)
        run = imported.json()["run"]

    assert imported.status_code == 201
    assert (run["origin"], run["state"]) == ("imported", "succeeded")
    assert (run["verification_status"], run["headline"]) == ("passed", _RECORDED_ENERGY)


def test_recorded_package_is_rerun_now_with_the_recorded_answer(
    tmp_path: Path, recorded_package: bytes
) -> None:
    with signed_in_api(tmp_path) as bench:
        imported = bench.post(_IMPORTS, content=recorded_package).json()["run"]
        source = read_run(bench, imported["identifier"])["input"]["text"].encode()
        rerun = solved(bench, source, "rerun-of-recorded-package", imported["identifier"])["run"]
        compared = {"base": imported["identifier"], "other": rerun["identifier"]}
        comparison = bench.get(_COMPARISONS, params=compared).json()

    (energy,) = comparison["answers"]
    assert (rerun["state"], rerun["verification_status"]) == ("succeeded", "passed")
    assert rerun["canonical_problem_sha256"] == imported["canonical_problem_sha256"]
    assert (energy["ratio"], comparison["input_differences"]) == ("1", [])


def test_recorded_altered_package_is_still_refused_before_anything_is_stored(
    tmp_path: Path, evidence: Path
) -> None:
    altered = (evidence / "electron_box_1nm.altered_package.zip").read_bytes()

    with signed_in_api(tmp_path) as bench:
        response = bench.post(_IMPORTS, content=altered)
        history = bench.get(RUNS).json()["runs"]

    refusal = response.json()
    assert (response.status_code, refusal["code"]) == (422, "package_refused")
    assert _ALTERED_ARTIFACT in refusal["message"]
    assert history == []


def test_recorded_manifest_is_the_one_inside_the_recorded_package(
    evidence: Path, recorded_package: bytes
) -> None:
    with zipfile.ZipFile(io.BytesIO(recorded_package)) as archive:
        packaged = archive.read("manifest.json")

    assert (evidence / "electron_box_1nm.package.manifest.json").read_bytes() == packaged
