import ast
import sys
from pathlib import Path

import pytest

import quantum_calculator

SOURCE = Path(quantum_calculator.__file__).resolve().parent
PACKAGE = "quantum_calculator"
DYNAMIC_EVALUATION = {"eval", "exec", "sympify", "parse_expr"}


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text("utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def _imports_of(package: str) -> set[str]:
    imports: set[str] = set()
    for path in (SOURCE / package).rglob("*.py"):
        imports |= _imported_modules(path)
    return imports


@pytest.mark.parametrize(
    ("package", "allowed"), [("domain", ("domain",)), ("notation", ("domain", "notation"))]
)
def test_pure_package_imports_only_the_standard_library_and_its_allowed_packages(
    package: str, allowed: tuple[str, ...]
) -> None:
    prefixes = tuple(f"{PACKAGE}.{name}" for name in allowed)
    foreign = {
        module
        for module in _imports_of(package)
        if module.split(".")[0] not in sys.stdlib_module_names and not module.startswith(prefixes)
    }

    assert foreign == set()


def test_sympy_is_confined_to_the_algebra_bridge_solvers_and_verification() -> None:
    offenders = [
        str(path.relative_to(SOURCE))
        for path in SOURCE.rglob("*.py")
        if path.relative_to(SOURCE).parts[0] not in {"algebra", "solvers", "verification"}
        and any(module.split(".")[0] == "sympy" for module in _imported_modules(path))
    ]

    assert offenders == []


@pytest.mark.parametrize(
    ("package", "forbidden"),
    [
        (
            "catalog",
            ("application", "interfaces", "adapters", "algebra", "solvers", "verification"),
        ),
        ("application", ("interfaces", "adapters", "algebra", "solvers", "verification")),
        (
            "algebra",
            ("application", "interfaces", "adapters", "catalog", "solvers", "verification"),
        ),
        ("solvers", ("application", "interfaces", "adapters", "catalog", "verification")),
        ("verification", ("application", "interfaces", "adapters", "catalog", "solvers")),
        (
            "adapters",
            ("application", "interfaces", "catalog", "algebra", "solvers", "verification"),
        ),
    ],
)
def test_inner_packages_do_not_import_outer_ones(package: str, forbidden: tuple[str, ...]) -> None:
    prefixes = tuple(f"{PACKAGE}.{name}" for name in forbidden)

    assert {module for module in _imports_of(package) if module.startswith(prefixes)} == set()


def _referenced_names(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text("utf-8"))
    names = [(node.id, node.lineno) for node in ast.walk(tree) if isinstance(node, ast.Name)]
    attributes = [
        (node.attr, node.lineno) for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    ]
    return names + attributes


def test_no_module_evaluates_text_as_a_program() -> None:
    offenders = [
        f"{path.relative_to(SOURCE)}:{line}"
        for path in SOURCE.rglob("*.py")
        for name, line in _referenced_names(path)
        if name in DYNAMIC_EVALUATION
    ]

    assert offenders == []
