import hashlib
import json
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.history_restore import HistoryBackupReader
from quantum_calculator.adapters.storage.migrations import SCHEMA_VERSION
from quantum_calculator.interfaces.api.documents import API_PREFIX
from support.api import RUNS, Json, read_run, signed_in_api, solved
from support.history import HISTORY, back_up

_EARLIER_HISTORY = Path(__file__).resolve().parents[1] / "fixtures" / "history_0_4_0"
_RECORDED = "expected.json"
_WRITTEN_BY = "0.4.0"
_WITNESS_CARD = "quantum.infinite_square_well.energy_level"


def _recorded_runs() -> list[Json]:
    recorded: list[Json] = json.loads((_EARLIER_HISTORY / _RECORDED).read_text("utf-8"))["runs"]
    return recorded


def _stored_files(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((directory / "artifacts").rglob("*"))
        if path.is_file()
    }


def _assert_reads_as_recorded(directory: Path) -> None:
    with signed_in_api(directory) as client:
        for recorded in _recorded_runs():
            identifier = recorded["details"]["run"]["identifier"]
            assert read_run(client, identifier) == recorded["details"]
            for name, table in recorded["tables"].items():
                assert client.get(f"{RUNS}/{identifier}/tables/{name}").json() == table


@pytest.fixture
def isolated_copy(tmp_path: Path) -> Path:
    copy = tmp_path / "isolated-copy"
    shutil.copytree(_EARLIER_HISTORY, copy, ignore=shutil.ignore_patterns(_RECORDED))
    return copy


def test_the_earlier_history_was_written_with_a_schema_this_version_reads(
    isolated_copy: Path,
) -> None:
    with closing(sqlite3.connect(isolated_copy / HISTORY)) as stored:
        (written_with,) = stored.execute("PRAGMA user_version").fetchone()

    assert 1 <= written_with <= SCHEMA_VERSION


def test_every_run_of_the_earlier_history_reads_as_it_was_recorded(isolated_copy: Path) -> None:
    _assert_reads_as_recorded(isolated_copy)


def test_the_earlier_runs_keep_the_version_that_calculated_them(isolated_copy: Path) -> None:
    with signed_in_api(isolated_copy) as client:
        runs = client.get(RUNS).json()["runs"]

    assert len(runs) == len(_recorded_runs())
    assert {run["package_version"] for run in runs} == {_WRITTEN_BY}


def test_opening_the_earlier_history_changes_no_stored_file(isolated_copy: Path) -> None:
    before = _stored_files(isolated_copy)

    with signed_in_api(isolated_copy) as client:
        client.get(RUNS)

    assert _stored_files(isolated_copy) == before == _stored_files(_EARLIER_HISTORY)


def test_rerunning_an_earlier_run_names_the_version_change_and_repeats_the_answer(
    isolated_copy: Path,
) -> None:
    witness = next(
        recorded["details"]
        for recorded in _recorded_runs()
        if recorded["details"]["run"]["card"]["identifier"] == _WITNESS_CARD
        and recorded["details"]["run"]["origin"] == "local"
        and recorded["details"]["run"]["parent_identifier"] is None
    )
    base = witness["run"]["identifier"]

    with signed_in_api(isolated_copy) as client:
        rerun = solved(client, witness["input"]["text"].encode("utf-8"), "rehearsal-0001", base)
        comparison = client.get(
            f"{API_PREFIX}/comparisons", params={"base": base, "other": rerun["run"]["identifier"]}
        ).json()

    calculator = [
        divergence
        for divergence in comparison["version_divergences"]
        if divergence["subject"] == "calculadora"
    ]
    assert rerun["run"]["state"] == "succeeded"
    assert rerun["run"]["package_version"] != _WRITTEN_BY
    assert calculator == [
        {"subject": "calculadora", "base": _WRITTEN_BY, "other": rerun["run"]["package_version"]}
    ]
    assert comparison["input_differences"] == []
    assert [answer["ratio"] for answer in comparison["answers"]] == ["1"]


def test_a_copy_of_the_earlier_history_restores_the_same_records(
    isolated_copy: Path, tmp_path: Path
) -> None:
    back_up(isolated_copy, tmp_path / "history.zip")

    report = HistoryBackupReader().restore(tmp_path / "history.zip", tmp_path / "restored")

    assert report.runs == len(_recorded_runs())
    assert _stored_files(tmp_path / "restored") == _stored_files(_EARLIER_HISTORY)
    _assert_reads_as_recorded(tmp_path / "restored")
