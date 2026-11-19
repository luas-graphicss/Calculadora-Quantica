import argparse
from pathlib import Path

from quantum_calculator.application.statements.budget import (
    DEFAULT_WALL_SECONDS,
    MAX_WALL_SECONDS,
)
from quantum_calculator.interfaces.cli.rendering.renderer import OutputFormat
from quantum_calculator.interfaces.serialization.schema_files import SCHEMA_NAMES

_TIME_LIMIT_FORM = f"o limite deve ser um número de segundos maior que 0 e até {MAX_WALL_SECONDS:g}"
_ANY_FREE_PORT = 0
_HIGHEST_PORT = 65535
_PORT_FORM = f"a porta deve ser um inteiro de {_ANY_FREE_PORT} a {_HIGHEST_PORT}"


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
    _add_serve_command(
        commands.add_parser(
            "serve",
            help="abre a bancada no navegador: catálogo, editor, resultados e histórico",
        )
    )
    _add_history_command(
        commands.add_parser(
            "backup", help="grava uma cópia conferida do histórico e dos artefatos em um arquivo"
        ),
        "arquivo ZIP a criar; um arquivo que já existe não é sobrescrito",
    )
    _add_history_command(
        commands.add_parser(
            "restore", help="restaura uma cópia do histórico em uma pasta nova ou vazia"
        ),
        "arquivo ZIP gravado por qcalc backup",
    )
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


def _add_history_command(command: argparse.ArgumentParser, archive_help: str) -> None:
    command.add_argument("archive", type=Path, metavar="ARQUIVO", help=archive_help)
    _add_data_directory(command)


def _add_data_directory(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        metavar="PASTA",
        help=(
            "pasta do histórico e dos artefatos (padrão: quantum-calculator dentro de "
            "$XDG_DATA_HOME ou de ~/.local/share)"
        ),
    )


def _add_serve_command(command: argparse.ArgumentParser) -> None:
    _add_data_directory(command)
    command.add_argument(
        "--port",
        type=_port,
        default=_ANY_FREE_PORT,
        metavar="PORTA",
        help="porta em 127.0.0.1; 0 escolhe uma porta livre (padrão: 0)",
    )
    command.add_argument(
        "--no-browser",
        action="store_true",
        help="não abre o navegador; o caminho do arquivo de acesso é impresso",
    )
    command.add_argument(
        "--web-root",
        type=Path,
        default=None,
        metavar="PASTA",
        help="pasta com a interface compilada (padrão: a que acompanha a instalação)",
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


def _port(text: str) -> int:
    try:
        port = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(_PORT_FORM) from error
    if not _ANY_FREE_PORT <= port <= _HIGHEST_PORT:
        raise argparse.ArgumentTypeError(_PORT_FORM)
    return port
