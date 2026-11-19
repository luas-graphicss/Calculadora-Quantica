import os
from pathlib import Path

_APPLICATION_DIRECTORY = "quantum-calculator"
_DATA_HOME_VARIABLE = "XDG_DATA_HOME"


def default_data_directory() -> Path:
    configured = Path(os.environ.get(_DATA_HOME_VARIABLE, ""))
    data_home = configured if configured.is_absolute() else Path.home() / ".local" / "share"
    return data_home / _APPLICATION_DIRECTORY
