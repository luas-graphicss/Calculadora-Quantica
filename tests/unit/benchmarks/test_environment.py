from benchmarks.harness.environment import Machine, describe_machine, profile_differences
from benchmarks.harness.protocol import MachineProfile

GIBIBYTE = 1024**3
PROFILE = MachineProfile(
    architecture="x86_64",
    logical_cpus=4,
    memory_gibibytes=8,
    operating_system="Ubuntu 24.04",
    python="CPython 3.12",
)


def machine(
    logical_cpus: int = 4,
    memory_bytes: int = int(7.75 * GIBIBYTE),
    memory_limit_bytes: int | None = None,
    operating_system: str = "Ubuntu 24.04.3 LTS",
) -> Machine:
    return Machine(
        architecture="x86_64",
        cpu_model="AMD EPYC 7763 64-Core Processor",
        logical_cpus=logical_cpus,
        memory_bytes=memory_bytes,
        memory_limit_bytes=memory_limit_bytes,
        operating_system=operating_system,
        kernel="6.8.0",
        python="CPython 3.12.3",
        linear_algebra_threads={"OPENBLAS_NUM_THREADS": "1"},
    )


def test_machine_with_the_reference_resources_matches_the_profile() -> None:
    assert profile_differences(machine(), PROFILE) == []


def test_machine_with_fewer_processors_is_reported_as_another_profile() -> None:
    (difference,) = profile_differences(machine(logical_cpus=2), PROFILE)

    assert difference == {"attribute": "logical_cpus", "found": "2", "reference": "4"}


def test_larger_memory_is_not_the_profile_unless_a_control_group_caps_it() -> None:
    larger = machine(memory_bytes=16 * GIBIBYTE)
    capped = machine(memory_bytes=16 * GIBIBYTE, memory_limit_bytes=8 * GIBIBYTE)

    assert [found["attribute"] for found in profile_differences(larger, PROFILE)] == [
        "memory_gibibytes"
    ]
    assert profile_differences(capped, PROFILE) == []


def test_another_operating_system_is_reported() -> None:
    (difference,) = profile_differences(machine(operating_system="Amazon Linux 2023"), PROFILE)

    assert difference["attribute"] == "operating_system"


def test_this_machine_is_described_with_a_processor_and_its_memory() -> None:
    described = describe_machine()

    assert described["logical_cpus"] >= 1
    assert described["memory_bytes"] > 0
    assert described["cpu_model"]
