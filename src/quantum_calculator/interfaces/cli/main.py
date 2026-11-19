import argparse
import io
import sys
from collections.abc import Sequence
from importlib import metadata

from quantum_calculator.adapters.execution.runtime_environment import PACKAGE_NAME
from quantum_calculator.application.statements.budget import symbolic_budget
from quantum_calculator.composition import build_calculator
from quantum_calculator.interfaces.cli.cancellation import interrupt_cancellation
from quantum_calculator.interfaces.cli.data_directory import default_data_directory
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
    if arguments.command == "serve":
        return _serve(arguments)
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


def _serve(arguments: argparse.Namespace) -> ExitCode:
    from quantum_calculator.interfaces.api.server import ServerOptions
    from quantum_calculator.interfaces.api.web_interface import packaged_interface
    from quantum_calculator.interfaces.cli.serve_command import ServeCommand

    options = ServerOptions(
        data_directory=arguments.data_dir or default_data_directory(),
        port=arguments.port,
        web_root=arguments.web_root or packaged_interface(),
        opens_browser=not arguments.no_browser,
    )
    return ServeCommand(sys.stdout, sys.stderr).run(options)


def _write_utf8(*streams: object) -> None:
    for stream in streams:
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
