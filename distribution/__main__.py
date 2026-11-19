import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from distribution.bundle import archive_bundle, build_bundle
from distribution.checksums import changed_files
from distribution.documents import DistributionError

_FAILED = 1
_ROOT = Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "verify":
            return _verify(arguments.bundle)
        return _build(arguments.root, arguments.output)
    except DistributionError as failure:
        sys.stderr.write(f"distribution: {failure}\n")
        return _FAILED


def _build(root: Path, output: Path) -> int:
    bundle = build_bundle(root, output, datetime.now(UTC))
    archive, digest = archive_bundle(bundle)
    sys.stdout.write(f"Distribuição montada em {bundle}\nArquivo: {archive}\nSHA-256: {digest}\n")
    return 0


def _verify(bundle: Path) -> int:
    changed = changed_files(bundle)
    for path in changed:
        sys.stderr.write(f"{path}: não confere com o hash registrado\n")
    if changed:
        return _FAILED
    sys.stdout.write(f"Todos os arquivos de {bundle} conferem com os hashes registrados.\n")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m distribution",
        description="Monta e confere a distribuição offline da Calculadora Quântica.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="comando")
    build = commands.add_parser(
        "build", help="monta o pacote offline com wheels, hashes, manifesto e licenças"
    )
    build.add_argument("output", type=Path, help="pasta onde o pacote e o arquivo são gravados")
    build.add_argument(
        "--root", type=Path, default=_ROOT, help="raiz do repositório (padrão: a desta ferramenta)"
    )
    verify = commands.add_parser("verify", help="confere cada arquivo de um pacote com o hash")
    verify.add_argument("bundle", type=Path, help="pasta do pacote offline")
    return parser


if __name__ == "__main__":
    sys.exit(main())
