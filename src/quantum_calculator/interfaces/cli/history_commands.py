from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from quantum_calculator.adapters.execution.runtime_environment import PACKAGE_NAME
from quantum_calculator.adapters.storage.history_backup import HistoryBackupWriter
from quantum_calculator.adapters.storage.history_restore import HistoryBackupReader
from quantum_calculator.domain.workbench.backups import BackupRejectedError, RestoreReport
from quantum_calculator.interfaces.cli.exit_codes import ExitCode


class HistoryCommands:
    def __init__(self, stdout: TextIO, stderr: TextIO, version: str) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self._version = version

    def back_up(self, data_directory: Path, destination: Path) -> ExitCode:
        writer = HistoryBackupWriter(PACKAGE_NAME, self._version)
        try:
            report = writer.write(data_directory, destination, datetime.now(UTC))
        except BackupRejectedError as refusal:
            return self._refuse(refusal.reason)
        except OSError as failure:
            return self._refuse(
                f"O sistema recusou a gravação ({failure.strerror}); a cópia não foi gravada."
            )
        self._stdout.write(
            f"Cópia gravada em {destination}\n"
            f"  execuções: {report.runs}\n"
            f"  artefatos: {report.artifacts}, cada um conferido com o próprio hash\n"
            f"  tamanho: {report.size} bytes\n"
        )
        return ExitCode.SUCCESS

    def restore(self, backup: Path, data_directory: Path) -> ExitCode:
        try:
            report = HistoryBackupReader().restore(backup, data_directory)
        except BackupRejectedError as refusal:
            return self._refuse(refusal.reason)
        except OSError as failure:
            return self._refuse(
                f"O sistema recusou a gravação ({failure.strerror}); nada foi restaurado."
            )
        self._stdout.write(
            f"Histórico restaurado em {data_directory}\n"
            f"  execuções: {report.runs}\n"
            f"  artefatos: {report.artifacts}, cada um conferido com o próprio hash\n"
            f"  {self._written_by(report)}\n"
            f"  {_storage_schema(report)}\n"
        )
        return ExitCode.SUCCESS

    def _written_by(self, report: RestoreReport) -> str:
        if report.written_by == self._version:
            return f"cópia gravada por esta mesma versão, {self._version}"
        return (
            f"cópia gravada pela versão {report.written_by}; esta instalação é a versão "
            f"{self._version}, e cada execução continua com a versão que a calculou"
        )

    def _refuse(self, reason: str) -> ExitCode:
        self._stderr.write(f"qcalc: {reason}\n")
        return ExitCode.HISTORY_REFUSED


def _storage_schema(report: RestoreReport) -> str:
    if report.storage_schema == report.current_storage_schema:
        return f"esquema de armazenamento {report.storage_schema}, o mesmo desta versão"
    return (
        f"esquema de armazenamento {report.storage_schema} migrado para o esquema "
        f"{report.current_storage_schema} desta versão"
    )
