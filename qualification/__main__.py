import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from qualification.calculator import Calculator
from qualification.case_matrix import build_matrix, is_homologated
from qualification.documents import CaseMatrix
from qualification.rendering import render_matrix, render_reproduction
from qualification.reproduction import is_reproduced, reproduce

_DIVERGED = 1
_ROOT = Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "matrix":
        return _matrix(arguments)
    return _reproduce(arguments)


def _matrix(arguments: argparse.Namespace) -> int:
    matrix = build_matrix(arguments.root, Calculator(str(arguments.qcalc)))
    _write_json(arguments.output, matrix)
    rendered = render_matrix(matrix)
    if arguments.markdown is not None:
        arguments.markdown.write_text(rendered, "utf-8")
    for case in matrix["cases"]:
        if case["disagreements"]:
            sys.stderr.write(
                f"{case['expectation']['identifier']}: {'; '.join(case['disagreements'])}\n"
            )
    for coverage in matrix["coverage"]:
        if coverage["gaps"]:
            sys.stderr.write(f"{coverage['card']}: {'; '.join(coverage['gaps'])}\n")
    sys.stdout.write(
        f"{len(matrix['cases'])} casos e {len(matrix['coverage'])} fichas em {arguments.output}\n"
    )
    return 0 if is_homologated(matrix) else _DIVERGED


def _reproduce(arguments: argparse.Namespace) -> int:
    matrix: CaseMatrix = json.loads(arguments.matrix.read_text("utf-8"))
    report = reproduce(arguments.root, matrix, str(arguments.qcalc), arguments.package)
    _write_json(arguments.output, report)
    sys.stdout.write(render_reproduction(report))
    return 0 if is_reproduced(report) else _DIVERGED


def _write_json(path: Path, document: object) -> None:
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", "utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m qualification",
        description=(
            "Roda o corpus de referência pelo comando qcalc: monta a matriz de casos da "
            "homologação ou confere outra instalação contra ela."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="comando")
    matrix = commands.add_parser(
        "matrix", help="compara cada caso com o oráculo e grava a matriz de casos"
    )
    matrix.add_argument("output", type=Path, help="arquivo JSON da matriz")
    matrix.add_argument("--markdown", type=Path, help="grava também a matriz em Markdown")
    reproduction = commands.add_parser(
        "reproduce", help="reexecuta o corpus nesta instalação e compara com a matriz"
    )
    reproduction.add_argument("matrix", type=Path, help="matriz de casos da homologação")
    reproduction.add_argument("output", type=Path, help="arquivo JSON do relatório")
    reproduction.add_argument(
        "--package",
        type=Path,
        action="append",
        default=[],
        help="pacote de reprodução a importar e reexecutar; pode ser repetido",
    )
    for command in (matrix, reproduction):
        command.add_argument(
            "--qcalc",
            type=Path,
            default=Path(sys.executable).with_name("qcalc"),
            help="comando qcalc a exercitar (padrão: o do ambiente que roda esta ferramenta)",
        )
        command.add_argument(
            "--root",
            type=Path,
            default=_ROOT,
            help="pasta que contém reference_cases (padrão: a que contém esta ferramenta)",
        )
    return parser


if __name__ == "__main__":
    sys.exit(main())
