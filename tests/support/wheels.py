import zipfile
from pathlib import Path


def write_wheel(
    directory: Path,
    name: str,
    version: str,
    metadata: str,
    licenses: dict[str, str] | None = None,
) -> Path:
    wheel = directory / f"{name}-{version}-py3-none-any.whl"
    dist_info = f"{name}-{version}.dist-info"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(f"{name}/__init__.py", "")
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n{metadata}",
        )
        for member, text in (licenses or {}).items():
            archive.writestr(f"{dist_info}/{member}", text)
    return wheel
