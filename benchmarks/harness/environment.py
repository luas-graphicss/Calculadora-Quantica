import os
import platform
import re
from pathlib import Path
from typing import TypedDict

from benchmarks.harness.protocol import MachineProfile

THREAD_VARIABLES = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")

_GIBIBYTE = 1024**3
_KIBIBYTE = 1024
_CPU_MODEL = re.compile(r"^model name\s*:\s*(.+)$", re.MULTILINE)
_TOTAL_MEMORY = re.compile(r"^MemTotal:\s+(\d+) kB$", re.MULTILINE)
_PRETTY_NAME = re.compile(r'^PRETTY_NAME="?([^"\n]+)"?$', re.MULTILINE)
_UNIFIED_GROUP = re.compile(r"^0::(.+)$", re.MULTILINE)
_UNKNOWN = "unknown"


class Machine(TypedDict):
    architecture: str
    cpu_model: str
    logical_cpus: int
    memory_bytes: int
    memory_limit_bytes: int | None
    operating_system: str
    kernel: str
    python: str
    linear_algebra_threads: dict[str, str | None]


class ProfileDifference(TypedDict):
    attribute: str
    found: str
    reference: str


def pin_linear_algebra_threads(count: int) -> None:
    for variable in THREAD_VARIABLES:
        os.environ[variable] = str(count)


def describe_machine() -> Machine:
    return Machine(
        architecture=platform.machine(),
        cpu_model=_first(_CPU_MODEL, Path("/proc/cpuinfo")),
        logical_cpus=len(os.sched_getaffinity(0)),
        memory_bytes=int(_first(_TOTAL_MEMORY, Path("/proc/meminfo"))) * _KIBIBYTE,
        memory_limit_bytes=_control_group_memory_limit(),
        operating_system=_first(_PRETTY_NAME, Path("/etc/os-release")),
        kernel=platform.release(),
        python=f"{platform.python_implementation()} {platform.python_version()}",
        linear_algebra_threads={name: os.environ.get(name) for name in THREAD_VARIABLES},
    )


def profile_differences(machine: Machine, profile: MachineProfile) -> list[ProfileDifference]:
    usable = min(machine["memory_bytes"], machine["memory_limit_bytes"] or machine["memory_bytes"])
    gibibytes = usable / _GIBIBYTE
    compared = (
        (
            "architecture",
            machine["architecture"],
            profile["architecture"],
            machine["architecture"] == profile["architecture"],
        ),
        (
            "logical_cpus",
            str(machine["logical_cpus"]),
            str(profile["logical_cpus"]),
            machine["logical_cpus"] == profile["logical_cpus"],
        ),
        (
            "memory_gibibytes",
            f"{gibibytes:.2f}",
            str(profile["memory_gibibytes"]),
            profile["memory_gibibytes"] - 1 < gibibytes <= profile["memory_gibibytes"],
        ),
        (
            "operating_system",
            machine["operating_system"],
            profile["operating_system"],
            machine["operating_system"].startswith(profile["operating_system"]),
        ),
        (
            "python",
            machine["python"],
            profile["python"],
            machine["python"].startswith(profile["python"]),
        ),
    )
    return [
        ProfileDifference(attribute=attribute, found=found, reference=reference)
        for attribute, found, reference, matches in compared
        if not matches
    ]


def _first(pattern: re.Pattern[str], source: Path) -> str:
    try:
        match = pattern.search(source.read_text("utf-8", "replace"))
    except OSError:
        return _UNKNOWN
    return _UNKNOWN if match is None else match.group(1).strip()


def _control_group_memory_limit() -> int | None:
    group = _first(_UNIFIED_GROUP, Path("/proc/self/cgroup"))
    if group == _UNKNOWN:
        return None
    try:
        limit = (Path("/sys/fs/cgroup") / group.lstrip("/") / "memory.max").read_text("ascii")
    except OSError:
        return None
    return int(limit) if limit.strip().isdigit() else None
