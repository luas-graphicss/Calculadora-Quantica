from pathlib import Path

import pytest

from quantum_calculator.adapters.storage.sqlite_runs import SqliteRunRepository
from support.cli import CliRunner
from support.history import HISTORY, back_up, recorded_history

_HISTORY_REFUSED = 11


def test_backup_and_restore_carry_the_history_to_another_directory(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    origin = recorded_history(tmp_path / "origin").runs.recent()
    archive = tmp_path / "history.zip"

    copied = run_cli("backup", archive, "--data-dir", tmp_path / "origin")
    restored = run_cli("restore", archive, "--data-dir", tmp_path / "restored")

    assert (copied.exit_code, copied.stderr) == (0, "")
    assert f"Cópia gravada em {archive}" in copied.stdout
    assert "execuções: 2" in copied.stdout
    assert (restored.exit_code, restored.stderr) == (0, "")
    assert "execuções: 2" in restored.stdout
    assert "o mesmo desta versão" in restored.stdout
    assert "gravada por esta mesma versão" in restored.stdout
    assert SqliteRunRepository(tmp_path / "restored" / HISTORY).recent() == origin


def test_restore_names_the_version_that_wrote_the_copy(run_cli: CliRunner, tmp_path: Path) -> None:
    recorded_history(tmp_path / "origin")
    back_up(tmp_path / "origin", tmp_path / "history.zip", version="0.3.0")

    restored = run_cli("restore", tmp_path / "history.zip", "--data-dir", tmp_path / "restored")

    assert restored.exit_code == 0
    assert "cópia gravada pela versão 0.3.0; esta instalação é a versão" in restored.stdout


def test_restore_refuses_a_directory_that_already_holds_research(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    recorded_history(tmp_path / "origin")
    run_cli("backup", tmp_path / "history.zip", "--data-dir", tmp_path / "origin")

    refused = run_cli("restore", tmp_path / "history.zip", "--data-dir", tmp_path / "origin")

    assert refused.exit_code == _HISTORY_REFUSED
    assert refused.stdout == ""
    assert refused.stderr.startswith("qcalc: A pasta ")
    assert "já tem conteúdo" in refused.stderr


def test_backup_refuses_a_directory_without_a_history(run_cli: CliRunner, tmp_path: Path) -> None:
    refused = run_cli("backup", tmp_path / "history.zip", "--data-dir", tmp_path)

    assert refused.exit_code == _HISTORY_REFUSED
    assert refused.stdout == ""
    assert "não tem histórico" in refused.stderr
    assert not (tmp_path / "history.zip").exists()


def test_backup_reads_the_default_data_directory(
    run_cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    recorded_history(tmp_path / "quantum-calculator")

    copied = run_cli("backup", tmp_path / "history.zip")

    assert copied.exit_code == 0
    assert (tmp_path / "history.zip").is_file()
