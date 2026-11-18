import io
import sys
from collections.abc import Sequence
from importlib import metadata

from quantum_calculator.adapters.execution.runtime_environment import PACKAGE_NAME
from quantum_calculator.application.statements.budget import symbolic_budget
from quantum_calculator.composition import build_calculator
from quantum_calculator.interfaces.cli.cancellation import interrupt_cancellation
from quantum_calculator.interfaces.cli.exit_codes import ExitCode
from quantum_calculator.interfaces.cli.parser import build_parser
from quantum_calculator.interfaces.cli.problem_commands import ProblemCommands
from quantum_calculator.interfaces.cli.rendering.renderer import renderer_for
from quantum_calculator.interfaces.serialization.schema_files import read_schema


def main(argv: Sequence[str] | None = None) -> int:
    _write_utf8(sys.stdout, sys.stderr)
    arguments = build_parser(metadata.version(PACKAGE_NAME)).parse_args(argv)
    if arguments.command == "schema":
        sys.stdout.write(read_schema(arguments.name))
        return ExitCode.SUCCESS
    if arguments.command == "catalog":
        listed = build_calculator()
        renderer = renderer_for(arguments.output_format, listed.units)
        sys.stdout.write(renderer.catalog(listed.catalog))
        return ExitCode.SUCCESS
    calculator = build_calculator(symbolic_budget(arguments.time_limit))
    with interrupt_cancellation() as cancellation:
        commands = ProblemCommands(
            calculator,
            renderer_for(arguments.output_format, calculator.units),
            sys.stdout,
            sys.stderr,
            cancellation,
        )
        if arguments.command == "validate":
            return commands.validate(arguments.path)
        return commands.solve(arguments.path)


def _write_utf8(*streams: object) -> None:
    for stream in streams:
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
