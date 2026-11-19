from pathlib import Path

import pytest

from distribution.__main__ import main
from distribution.checksums import describe_files, write_checksums
from distribution.documents import MANIFEST_NAME


def _bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "requirements.txt").write_text("numpy==2.5.5\n", "utf-8")
    (bundle / MANIFEST_NAME).write_text("{}\n", "utf-8")
    write_checksums(bundle, describe_files(bundle))
    return bundle


def test_verify_accepts_a_bundle_whose_files_match_the_recorded_digests(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bundle = _bundle(tmp_path)

    assert main(["verify", str(bundle)]) == 0
    assert "conferem com os hashes registrados" in capsys.readouterr().out


def test_verify_names_the_altered_file_and_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bundle = _bundle(tmp_path)
    (bundle / "requirements.txt").write_text("numpy==2.5.6\n", "utf-8")

    assert main(["verify", str(bundle)]) == 1
    captured = capsys.readouterr()
    assert captured.err == "requirements.txt: não confere com o hash registrado\n"
    assert captured.out == ""
