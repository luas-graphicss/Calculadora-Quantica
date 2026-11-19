from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    from quantum_calculator.interfaces.cli.main import main as run

    return run(argv)
