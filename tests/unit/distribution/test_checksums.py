from pathlib import Path

from distribution.checksums import changed_files, describe_files, sha256_of, write_checksums
from distribution.documents import CHECKSUMS_NAME, MANIFEST_NAME

_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def _bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    (bundle / "wheels").mkdir(parents=True)
    (bundle / "wheels" / "numpy.whl").write_bytes(b"wheel")
    (bundle / "install.sh").write_text("#!/bin/sh\n", "utf-8")
    (bundle / MANIFEST_NAME).write_text("{}\n", "utf-8")
    write_checksums(bundle, describe_files(bundle))
    return bundle


def test_the_digest_of_an_empty_file_is_the_published_constant(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.touch()

    assert sha256_of(empty) == _EMPTY_SHA256


def test_files_are_described_by_relative_path_without_the_manifest_and_the_checksums(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)

    described = describe_files(bundle)

    assert [file["path"] for file in described] == ["install.sh", "wheels/numpy.whl"]
    assert described[1]["size"] == len(b"wheel")
    assert described[1]["sha256"] == sha256_of(bundle / "wheels" / "numpy.whl")


def test_the_checksums_cover_every_file_and_the_manifest(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)

    listed = [
        line.partition("  ")[2]
        for line in (bundle / CHECKSUMS_NAME).read_text("utf-8").splitlines()
    ]

    assert listed == ["install.sh", "wheels/numpy.whl", MANIFEST_NAME]


def test_an_untouched_bundle_has_no_changed_file(tmp_path: Path) -> None:
    assert changed_files(_bundle(tmp_path)) == []


def test_an_altered_file_and_a_missing_file_are_both_named(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    (bundle / "wheels" / "numpy.whl").write_bytes(b"another wheel")
    (bundle / "install.sh").unlink()

    assert changed_files(bundle) == ["install.sh", "wheels/numpy.whl"]


def test_an_altered_manifest_is_named(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    (bundle / MANIFEST_NAME).write_text('{"version": "9.9.9"}\n', "utf-8")

    assert changed_files(bundle) == [MANIFEST_NAME]
