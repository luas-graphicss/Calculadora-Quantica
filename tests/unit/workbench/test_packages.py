import hashlib
import io
import json
import zipfile
from collections.abc import Callable
from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.zip_packages import ZipPackageArchive
from quantum_calculator.application.workbench.export_package import (
    ExportPackage,
    PackageGenerator,
    RunStillActiveError,
)
from quantum_calculator.application.workbench.import_package import ImportPackage
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.application.workbench.submit_run import Submission
from quantum_calculator.domain.execution import CalculationFailedError
from quantum_calculator.domain.workbench.documents import Document
from quantum_calculator.domain.workbench.packages import PackageRejectedError
from quantum_calculator.domain.workbench.runs import RunOrigin, RunState
from support.workbench import (
    RECORD,
    SOURCE,
    Bench,
    build_bench,
    finish,
    raising,
    sequential_identifiers,
)

_GENERATOR = PackageGenerator("quantum-calculator", "0.0.0-test")
_NUMERICAL_RECORD: Document = {
    **RECORD,
    "input": {"sha256": hashlib.sha256(SOURCE).hexdigest(), "text": SOURCE.decode()},
}

type Rewrite = Callable[[dict[str, bytes]], None]


@pytest.fixture
def origin(tmp_path: Path) -> Bench:
    return build_bench(tmp_path / "origin")


@pytest.fixture
def destination(tmp_path: Path) -> Bench:
    return build_bench(tmp_path / "destination")


def _exporter(bench: Bench) -> ExportPackage:
    return ExportPackage(ReadHistory(bench.runs, bench.artifacts), ZipPackageArchive(), _GENERATOR)


def _importer(bench: Bench) -> ImportPackage:
    return ImportPackage(
        bench.runs,
        bench.artifacts,
        ZipPackageArchive(),
        sequential_identifiers(),
        readable_record_versions=("1.0", "1.1", "1.2"),
    )


def _exported(bench: Bench, outcome: Document = _NUMERICAL_RECORD) -> bytes:
    identifier = finish(bench, "submission-key-0001", SOURCE, outcome)
    return _exporter(bench).execute(identifier).content


def _files(package: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _repacked(package: bytes, rewrite: Rewrite) -> bytes:
    files = _files(package)
    rewrite(files)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _with_manifest(change: Callable[[dict[str, object]], None]) -> Rewrite:
    def rewrite(files: dict[str, bytes]) -> None:
        manifest = json.loads(files["manifest.json"])
        change(manifest)
        files["manifest.json"] = json.dumps(manifest).encode()

    return rewrite


def test_a_package_holds_the_input_the_canonical_problem_the_record_and_csv_tables(
    origin: Bench,
) -> None:
    files = _files(_exported(origin))

    assert sorted(files) == [
        "answers.csv",
        "input.json",
        "manifest.json",
        "outcome.json",
        "problem.json",
        "tables/eigenfunctions.csv",
    ]
    assert files["input.json"] == SOURCE
    assert json.loads(files["outcome.json"]) == _NUMERICAL_RECORD
    assert "input" not in json.loads(files["problem.json"])


def test_the_manifest_lists_every_file_with_its_role_size_and_digest(origin: Bench) -> None:
    files = _files(_exported(origin))

    manifest = json.loads(files["manifest.json"])
    assert (manifest["document"], manifest["schema_version"]) == ("reproduction_package", "1.0")
    assert manifest["generator"] == {"name": "quantum-calculator", "version": "0.0.0-test"}
    assert manifest["canonical_problem_sha256"] == hashlib.sha256(files["problem.json"]).hexdigest()
    assert [(entry["path"], entry["role"]) for entry in manifest["files"]] == [
        ("answers.csv", "table"),
        ("input.json", "input"),
        ("outcome.json", "outcome"),
        ("problem.json", "problem"),
        ("tables/eigenfunctions.csv", "table"),
    ]
    for entry in manifest["files"]:
        content = files[entry["path"]]
        assert (entry["size"], entry["sha256"]) == (
            len(content),
            hashlib.sha256(content).hexdigest(),
        )
    assert manifest["run"]["state"] == "succeeded"
    assert manifest["run"]["verification_status"] == "passed"
    assert manifest["run"]["headline"] == "E_1 = 0.375000 eV"


def test_tables_are_exported_as_csv_with_the_unit_of_each_column(origin: Bench) -> None:
    files = _files(_exported(origin))

    assert files["tables/eigenfunctions.csv"].decode() == (
        "x [m],psi_1(x) [m^-1/2]\r\n0.0,0.0\r\n0.5,1.5\r\n1.0,0.0\r\n"
    )
    assert files["answers.csv"].decode() == (
        "grandeza,símbolo,descrição,valor,unidade,erro estimado,origem do erro\r\n"
        "energy_1,E_1,energia do nível 1,0.375000,eV,0.00050,refinamento\r\n"
    )


def test_a_package_carries_no_path_of_the_machine_that_wrote_it(
    origin: Bench, tmp_path: Path
) -> None:
    package = _exported(origin)

    for name, content in _files(package).items():
        assert not name.startswith("/")
        assert str(tmp_path).encode() not in content


def test_exporting_the_same_run_twice_gives_the_same_bytes(origin: Bench) -> None:
    identifier = finish(origin, "submission-key-0001", SOURCE, _NUMERICAL_RECORD)

    assert _exporter(origin).execute(identifier) == _exporter(origin).execute(identifier)
    assert _exporter(origin).execute(identifier).file_name == f"qcalc-{identifier}.zip"


def test_a_run_that_has_not_finished_cannot_be_exported(origin: Bench) -> None:
    queued = origin.submit.execute(Submission(SOURCE, "submission-key-0001", 30.0)).run

    with pytest.raises(RunStillActiveError):
        _exporter(origin).execute(queued.identifier)


def test_a_valid_package_rebuilds_the_run_in_an_empty_history_without_calculating(
    origin: Bench, destination: Bench
) -> None:
    package = _exported(origin)
    (exported,) = origin.runs.recent()

    receipt = _importer(destination).execute(package)

    imported = receipt.run
    history = ReadHistory(destination.runs, destination.artifacts)
    details = history.details(imported.identifier)
    assert receipt.created
    assert (imported.origin, imported.state) == (RunOrigin.IMPORTED, RunState.SUCCEEDED)
    assert (imported.headline, imported.verification_status) == (exported.headline, "passed")
    assert (imported.card_identifier, imported.package_version) == (
        exported.card_identifier,
        exported.package_version,
    )
    assert (imported.submitted_at, imported.finished_at) == (
        exported.submitted_at,
        exported.finished_at,
    )
    assert details.source == SOURCE
    assert history.complete_outcome(imported.identifier) == _NUMERICAL_RECORD
    assert destination.documents.calculated == []
    assert destination.queue.enqueued == []


def test_importing_the_same_package_twice_keeps_one_entry(
    origin: Bench, destination: Bench
) -> None:
    package = _exported(origin)
    importer = _importer(destination)
    first = importer.execute(package)

    second = importer.execute(package)

    assert not second.created
    assert second.run == first.run
    assert len(destination.runs.recent()) == 1


def test_an_imported_run_can_be_exported_again_with_the_same_content(
    origin: Bench, destination: Bench
) -> None:
    package = _exported(origin)
    imported = _importer(destination).execute(package).run

    again = _files(_exporter(destination).execute(imported.identifier).content)

    original = _files(package)
    for name in ("input.json", "problem.json", "outcome.json", "tables/eigenfunctions.csv"):
        assert again[name] == original[name]


def test_a_failed_run_travels_with_its_diagnostic(origin: Bench, destination: Bench) -> None:
    origin.documents.calculation = raising(CalculationFailedError(-9))
    failed = origin.submit.execute(Submission(SOURCE, "submission-key-0001", 30.0)).run
    origin.execute.execute(failed.identifier)

    imported = _importer(destination).execute(_exporter(origin).execute(failed.identifier).content)

    assert (imported.run.state, imported.run.failure_category) == (
        RunState.FAILED,
        "calculation_failed",
    )
    assert imported.run.verification_status is None


def _alter(name: str) -> Rewrite:
    def rewrite(files: dict[str, bytes]) -> None:
        files[name] += b" "

    return rewrite


def _drop(name: str) -> Rewrite:
    def rewrite(files: dict[str, bytes]) -> None:
        del files[name]

    return rewrite


def _add(name: str) -> Rewrite:
    def rewrite(files: dict[str, bytes]) -> None:
        files[name] = b"#!/bin/sh\n"

    return rewrite


def _declare(field: str, value: object) -> Rewrite:
    def change(manifest: dict[str, object]) -> None:
        manifest[field] = value

    return _with_manifest(change)


def _declare_state(state: str) -> Rewrite:
    def change(manifest: dict[str, object]) -> None:
        run = manifest["run"]
        assert isinstance(run, dict)
        run["state"] = state

    return _with_manifest(change)


@pytest.mark.parametrize(
    ("rewrite", "reason"),
    [
        (_alter("outcome.json"), "outcome.json não confere com o hash"),
        (_alter("tables/eigenfunctions.csv"), "tables/eigenfunctions.csv não confere com o hash"),
        (_drop("input.json"), "falta o arquivo input.json"),
        (_drop("manifest.json"), "falta o manifesto"),
        (_add("setup.sh"), "setup.sh não consta do manifesto"),
        (_declare("schema_version", "2.0"), "versão 2.0 do formato"),
        (_declare("document", "run_record"), "não descreve um pacote"),
        (_declare("canonical_problem_sha256", "0" * 64), "problema canônico não confere"),
        (_declare_state("running"), "ainda running"),
        (_declare_state("cancelled"), "cancelled não tem registro"),
        (_declare_state("failed"), "não corresponde a uma execução failed"),
        (_declare_state("finished"), "estado desconhecido finished"),
    ],
)
def test_a_package_that_fails_its_checks_is_refused_before_anything_is_stored(
    origin: Bench, destination: Bench, rewrite: Rewrite, reason: str
) -> None:
    package = _repacked(_exported(origin), rewrite)

    with pytest.raises(PackageRejectedError, match=reason) as refused:
        _importer(destination).execute(package)

    assert refused.value.reason.startswith("Pacote recusado:")
    assert refused.value.reason.endswith("Nada foi importado nem calculado.")
    assert destination.runs.recent() == ()
    assert destination.documents.calculated == []
    assert destination.queue.enqueued == []


def _consistently_replace_the_input(files: dict[str, bytes]) -> None:
    files["input.json"] = b'{"schema_version": "1.0", "problem": "another"}'
    manifest = json.loads(files["manifest.json"])
    for entry in manifest["files"]:
        if entry["path"] == "input.json":
            entry["size"] = len(files["input.json"])
            entry["sha256"] = hashlib.sha256(files["input.json"]).hexdigest()
    files["manifest.json"] = json.dumps(manifest).encode()


def test_a_record_calculated_from_another_input_is_refused_even_with_matching_hashes(
    origin: Bench, destination: Bench
) -> None:
    package = _repacked(_exported(origin), _consistently_replace_the_input)

    with pytest.raises(PackageRejectedError, match="calculado a partir de outra entrada"):
        _importer(destination).execute(package)

    assert destination.runs.recent() == ()


@pytest.mark.parametrize("version", ["1.0", "1.1", "1.2"])
def test_a_record_written_with_an_earlier_output_schema_stays_readable(
    origin: Bench, destination: Bench, version: str
) -> None:
    package = _exported(origin, {**_NUMERICAL_RECORD, "schema_version": version})

    imported = _importer(destination).execute(package).run

    assert imported.headline == "E_1 = 0.375000 eV"
    outcome = ReadHistory(destination.runs, destination.artifacts).complete_outcome(
        imported.identifier
    )
    assert outcome is not None
    assert outcome["schema_version"] == version


def test_a_record_written_with_a_newer_output_schema_is_refused(
    origin: Bench, destination: Bench
) -> None:
    package = _exported(origin, {**_NUMERICAL_RECORD, "schema_version": "9.0"})

    with pytest.raises(PackageRejectedError, match=r"versão 9\.0 do esquema de saída"):
        _importer(destination).execute(package)
