import json
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from quantum_calculator.adapters.storage.history_backup import HistoryBackupWriter
from quantum_calculator.domain.workbench.backups import BackupReport
from support.workbench import OTHER_SOURCE, RECORD, SOURCE, Bench, build_bench, finish

MANIFEST = "manifest.json"
HISTORY = "history.sqlite3"
GENERATOR = "quantum-calculator"
WRITTEN_BY = "1.0.0-test"
WRITTEN_AT = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)

type Members = dict[str, bytes]


def recorded_history(directory: Path) -> Bench:
    bench = build_bench(directory)
    finish(bench, "submission-key-0001", SOURCE, RECORD)
    finish(bench, "submission-key-0002", OTHER_SOURCE, RECORD)
    return bench


def back_up(directory: Path, destination: Path, version: str = WRITTEN_BY) -> BackupReport:
    return HistoryBackupWriter(GENERATOR, version).write(directory, destination, WRITTEN_AT)


def rewritten(archive: Path, destination: Path, change: Callable[[Members], None]) -> Path:
    with zipfile.ZipFile(archive) as source:
        members = {name: source.read(name) for name in source.namelist()}
    change(members)
    with zipfile.ZipFile(destination, "w") as target:
        for name, content in members.items():
            target.writestr(name, content)
    return destination


def with_manifest(members: Members, change: Callable[[dict[str, object]], None]) -> None:
    manifest = json.loads(members[MANIFEST])
    change(manifest)
    members[MANIFEST] = json.dumps(manifest).encode("utf-8")
