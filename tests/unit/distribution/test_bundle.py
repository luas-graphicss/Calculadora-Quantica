import tarfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from distribution import bundle as bundle_module
from distribution.bundle import archive_bundle, build_bundle
from distribution.checksums import sha256_of
from distribution.documents import DistributionError

_BUILT_AT = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "quantum-calculator"\nversion = "1.0.0rc1"\n', "utf-8"
    )
    return root


def _fail_to_build_the_wheel(root: Path, wheels: Path) -> Path:
    raise DistributionError(f"no wheel was built from {root} into {wheels}")


def test_a_build_that_fails_leaves_nothing_that_looks_like_a_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bundle_module, "build_project_wheel", _fail_to_build_the_wheel)
    output = tmp_path / "release"

    with pytest.raises(DistributionError, match="no wheel was built"):
        build_bundle(_root(tmp_path), output, _BUILT_AT)

    assert list(output.iterdir()) == []


def test_a_bundle_that_already_exists_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bundle_module, "build_project_wheel", _fail_to_build_the_wheel)
    output = tmp_path / "release"
    existing = output / f"quantum-calculator-1.0.0rc1-offline-{bundle_module._platform_tag()}"
    existing.mkdir(parents=True)
    (existing / "MANIFEST.json").write_text("{}\n", "utf-8")

    with pytest.raises(DistributionError, match="does not overwrite"):
        build_bundle(_root(tmp_path), output, _BUILT_AT)

    assert (existing / "MANIFEST.json").read_text("utf-8") == "{}\n"


def test_the_archive_is_published_with_its_digest_and_without_the_builder_account(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "quantum-calculator-1.0.0rc1-offline-linux_x86_64-cp312"
    (bundle / "wheels").mkdir(parents=True)
    (bundle / "install.sh").write_text("#!/bin/sh\n", "utf-8")

    archive, digest = archive_bundle(bundle)

    assert archive.name == f"{bundle.name}.tar.gz"
    assert digest == sha256_of(archive)
    published = archive.with_name(f"{archive.name}.sha256").read_text("utf-8")
    assert published == f"{digest}  {archive.name}\n"
    with tarfile.open(archive) as packed:
        members = packed.getmembers()
    assert f"{bundle.name}/install.sh" in [member.name for member in members]
    assert {(member.uid, member.gid, member.uname, member.gname) for member in members} == {
        (0, 0, "", "")
    }
