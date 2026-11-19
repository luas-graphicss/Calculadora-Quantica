import json
import subprocess
import sys
from pathlib import Path

import pytest

_CALCULATION_LIBRARIES = {"numpy", "scipy", "sympy", "fastapi", "uvicorn"}
_COMMAND_LINE = "quantum_calculator.interfaces.cli.main"
_AS_MODULE = 'runpy.run_module("quantum_calculator.__main__", run_name="__mp_main__")'
_AS_SCRIPT = (
    f'runpy.run_path({str(Path(sys.executable).with_name("qcalc"))!r}, run_name="__mp_main__")'
)


def _modules_loaded_by(restart: str) -> set[str]:
    probe = f"import json, runpy, sys\n{restart}\nprint(json.dumps(sorted(sys.modules)))\n"
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        check=True,
        encoding="utf-8",
        timeout=60,
    )
    loaded: list[str] = json.loads(completed.stdout)
    return set(loaded)


@pytest.mark.parametrize("restart", [_AS_MODULE, _AS_SCRIPT], ids=["module", "script"])
def test_a_calculation_process_restarts_the_entry_point_without_loading_the_command_line(
    restart: str,
) -> None:
    loaded = _modules_loaded_by(restart)

    assert "quantum_calculator.interfaces.cli.entry" in loaded
    assert _COMMAND_LINE not in loaded
    assert {name.partition(".")[0] for name in loaded} & _CALCULATION_LIBRARIES == set()
