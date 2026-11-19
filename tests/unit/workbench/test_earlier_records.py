import json
from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.zip_packages import ZipPackageArchive
from quantum_calculator.adapters.units.codata_2022 import Codata2022Constants
from quantum_calculator.adapters.units.si_registry import SiUnitRegistry
from quantum_calculator.application.workbench.compare_runs import CompareRuns, VersionDivergence
from quantum_calculator.application.workbench.display_answers import DisplayAnswers
from quantum_calculator.application.workbench.export_package import (
    ExportPackage,
    PackageGenerator,
)
from quantum_calculator.application.workbench.import_package import ImportPackage
from quantum_calculator.application.workbench.read_history import ReadHistory
from quantum_calculator.domain.workbench.documents import Document, text_member
from quantum_calculator.interfaces.serialization.encoding.common_sections import (
    READABLE_OUTPUT_SCHEMA_VERSIONS,
)
from support.workbench import Bench, build_bench, finish

_EARLIER_RECORDS = Path(__file__).resolve().parents[2] / "fixtures" / "earlier_records"


def _earlier(name: str) -> tuple[bytes, Document]:
    record: Document = json.loads((_EARLIER_RECORDS / name).read_text())
    source = text_member(record, "input", "text")
    assert source is not None
    return source.encode(), record


@pytest.fixture
def bench(tmp_path: Path) -> Bench:
    return build_bench(tmp_path / "origin")


def test_a_closed_form_record_written_with_schema_1_0_is_still_summarized_and_converted(
    bench: Bench,
) -> None:
    source, record = _earlier("run_record_1_0.json")
    history = ReadHistory(bench.runs, bench.artifacts)

    identifier = finish(bench, "submission-key-0001", source, record)

    converted = DisplayAnswers(history, SiUnitRegistry(Codata2022Constants())).execute(
        identifier, "meV"
    )
    assert record["schema_version"] == "1.0"
    assert history.run(identifier).headline == "E = 0.3760301621 eV"
    assert [(answer.value, answer.unit) for answer in converted.answers] == [("376.0301621", "meV")]


def test_a_symbolic_record_written_with_schema_1_1_is_still_summarized(bench: Bench) -> None:
    source, record = _earlier("statement_run_record_1_1.json")

    identifier = finish(bench, "submission-key-0001", source, record)

    run = ReadHistory(bench.runs, bench.artifacts).run(identifier)
    assert record["schema_version"] == "1.1"
    assert (run.headline, run.verification_status) == ("y(t) = y_0*exp(-k*t)", "passed")


def test_an_earlier_record_travels_in_a_package_and_shows_its_versions_before_a_comparison(
    bench: Bench, tmp_path: Path, repository_root: Path
) -> None:
    source, earlier = _earlier("run_record_1_0.json")
    current: Document = json.loads(
        (repository_root / "docs/evidence/phase-1/electron_box_1nm.run_record.json").read_text()
    )
    exported = ExportPackage(
        ReadHistory(bench.runs, bench.artifacts),
        ZipPackageArchive(),
        PackageGenerator("quantum-calculator", "0.1.0"),
    ).execute(finish(bench, "submission-key-0001", source, earlier))
    destination = build_bench(tmp_path / "destination")
    history = ReadHistory(destination.runs, destination.artifacts)

    imported = (
        ImportPackage(
            destination.runs,
            destination.artifacts,
            ZipPackageArchive(),
            destination.new_identifier,
            READABLE_OUTPUT_SCHEMA_VERSIONS,
        )
        .execute(exported.content)
        .run
    )
    recalculated = finish(destination, "submission-key-0002", source, current)

    comparison = CompareRuns(history, SiUnitRegistry(Codata2022Constants())).execute(
        imported.identifier, recalculated
    )
    assert history.complete_outcome(imported.identifier) == earlier
    assert VersionDivergence("esquema do registro", "1.0", "1.2") in comparison.version_divergences
    assert comparison.answers[0].ratio == "1"
    assert comparison.input_differences == ()
