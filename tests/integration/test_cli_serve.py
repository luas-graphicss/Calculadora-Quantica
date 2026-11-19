import socket
from pathlib import Path

import pytest

from quantum_calculator.interfaces.cli.data_directory import default_data_directory
from quantum_calculator.interfaces.cli.main import main
from support.cli import CliRunner


def test_the_data_directory_follows_the_xdg_data_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert default_data_directory() == tmp_path / "quantum-calculator"


@pytest.mark.parametrize("data_home", ["", "relative/data"])
def test_without_an_absolute_data_home_the_history_goes_under_the_home_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, data_home: str
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", data_home)

    assert default_data_directory() == tmp_path / ".local" / "share" / "quantum-calculator"


@pytest.mark.parametrize("port", ["-1", "65536", "http"])
def test_a_port_outside_the_range_is_refused_before_anything_starts(
    capsys: pytest.CaptureFixture[str], port: str
) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["serve", "--port", port])

    assert stopped.value.code == 2
    assert "a porta deve ser um inteiro de 0 a 65535" in capsys.readouterr().err


def test_a_port_already_in_use_is_reported_without_starting_the_bench(
    run_cli: CliRunner, tmp_path: Path
) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]

        result = run_cli("serve", "--no-browser", "--port", port, "--data-dir", tmp_path)

    assert result.exit_code == 10
    assert result.stdout == ""
    assert f"qcalc: a bancada não foi iniciada: a porta {port} não pôde ser aberta" in result.stderr
    assert not (tmp_path / "abrir-calculadora.html").exists()
