import argparse
from pathlib import Path

from quantum_calculator.interfaces.cli.rendering.renderer import OutputFormat
from quantum_calculator.interfaces.serialization.schema_files import SCHEMA_NAMES


def build_parser(version: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qcalc",
        description=(
            "Calculadora Quântica: resolve um problema físico descrito em JSON e mostra "
            "como conferir a resposta."
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
            help="resolve o problema e mostra resposta, memória de cálculo e verificação",
        )
    )
    schema = commands.add_parser("schema", help="imprime o esquema JSON da entrada ou da saída")
    schema.add_argument("name", choices=SCHEMA_NAMES, help="esquema a imprimir")
    return parser


def _add_problem_command(command: argparse.ArgumentParser) -> None:
    command.add_argument("path", type=Path, help="arquivo JSON com o problema")
    command.add_argument(
        "--format",
        dest="output_format",
        type=OutputFormat,
        choices=list(OutputFormat),
        default=OutputFormat.TEXT,
        help="formato da saída (padrão: text)",
    )
