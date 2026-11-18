from importlib import resources

SCHEMA_NAMES = ("problem", "statement", "output")
_PACKAGE = "quantum_calculator.interfaces.serialization.schemas"


def read_schema(name: str) -> str:
    return resources.files(_PACKAGE).joinpath(f"{name}.schema.json").read_text("utf-8")
