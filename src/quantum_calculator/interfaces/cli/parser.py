import argparse
from pathlib import Path

from quantum_calculator.application.statements.budget import (
    DEFAULT_WALL_SECONDS,
    MAX_WALL_SECONDS,
)
from quantum_calculator.interfaces.cli.rendering.renderer import OutputFormat
from quantum_calculator.interfaces.serialization.schema_files import SCHEMA_NAMES

_TIME_LIMIT_FORM = f"o limite deve ser um número de segundos maior que 0 e até {MAX_WALL_SECONDS:g}"


def build_parser(version: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qcalc",
        description=(
            "Calculadora Quântica: resolve um problema descrito em JSON, por ficha, por "
            "enunciado digitado ou por método numérico, e mostra como conferir a resposta."
        ),
    )
    parser.add_argument("--version", action="version", version=f"qcalc {version}")
    commands = parser.add_subparsers(dest="command", required=True, metavar="comando")
    _add_problem_command(
        commands.add_parser(
            "validate",
            help="confere a entrada e mostra a interpretação e o plano, sem calcular",
        )
    )
    _add_problem_command(
        commands.add_parser(
            "solve",
            help="resolve o problema ou revisa a candidata e mostra resposta e verificação",
        )
    )
    _add_format(commands.add_parser("catalog", help="lista as fichas homologadas e suas versões"))
    schema = commands.add_parser("schema", help="imprime o esquema JSON da entrada ou da saída")
    schema.add_argument("name", choices=SCHEMA_NAMES, help="esquema a imprimir")
    return parser


def _add_problem_command(command: argparse.ArgumentParser) -> None:
    command.add_argument("path", type=Path, help="arquivo JSON com o problema ou o enunciado")
    _add_format(command)
    command.add_argument(
        "--time-limit",
        type=_time_limit,
        default=DEFAULT_WALL_SECONDS,
        metavar="SEGUNDOS",
        help=(
            "tempo de relógio máximo do cálculo simbólico ou numérico, até "
            f"{MAX_WALL_SECONDS:g} (padrão: {DEFAULT_WALL_SECONDS:g})"
        ),
    )


def _add_format(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--format",
        dest="output_format",
        type=OutputFormat,
        choices=list(OutputFormat),
        default=OutputFormat.TEXT,
        help="formato da saída (padrão: text)",
    )


def _time_limit(text: str) -> float:
    try:
        seconds = float(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(_TIME_LIMIT_FORM) from error
    if not 0 < seconds <= MAX_WALL_SECONDS:
        raise argparse.ArgumentTypeError(_TIME_LIMIT_FORM)
    return seconds
