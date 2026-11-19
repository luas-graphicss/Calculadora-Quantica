import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from benchmarks.harness.baseline import render_comparison
from benchmarks.harness.protocol import REPOSITORY_ROOT
from benchmarks.harness.report import BenchmarkReport

_TARGET_MISSED = 1


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "compare":
        sys.stdout.write(render_comparison(_read(arguments.baseline), _read(arguments.candidate)))
        return 0
    return _measure(arguments.output, arguments.command_path)


def _measure(output: Path, command: Path) -> int:
    # Each worker re-imports this module, so the measuring code stays out of its start-up.
    from benchmarks.harness.measurement import measure
    from benchmarks.harness.summary import render_summary

    report = measure(REPOSITORY_ROOT, str(command), _announce)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", "utf-8")
    sys.stdout.write(render_summary(report))
    return 0 if all(verdict["met"] for verdict in report["targets"]) else _TARGET_MISSED


def _announce(workload: str) -> None:
    sys.stderr.write(f"measuring {workload}\n")


def _read(path: Path) -> BenchmarkReport:
    report: BenchmarkReport = json.loads(path.read_text("utf-8"))
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m benchmarks.harness",
        description="Mede as cargas homologadas e compara com a linha de base congelada.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="comando")
    measure = commands.add_parser("measure", help="mede as cargas e grava os dados brutos")
    measure.add_argument("output", type=Path, help="arquivo JSON dos dados brutos")
    measure.add_argument(
        "--qcalc",
        dest="command_path",
        type=Path,
        default=Path(sys.executable).with_name("qcalc"),
        help="comando qcalc a medir (padrão: o do ambiente que roda a medição)",
    )
    compare = commands.add_parser("compare", help="compara duas medições, carga a carga")
    compare.add_argument("baseline", type=Path, help="dados brutos da linha de base")
    compare.add_argument("candidate", type=Path, help="dados brutos da medição candidata")
    return parser


if __name__ == "__main__":
    sys.exit(main())
