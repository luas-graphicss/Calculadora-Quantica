#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "uso: ./install.sh PASTA_DE_INSTALACAO" >&2
    exit 2
fi

bundle=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
target=$1
python=${QCALC_PYTHON:-python3.12}

if [ -e "$target" ]; then
    echo "install.sh: $target já existe; escolha uma pasta nova." >&2
    exit 1
fi
if ! command -v "$python" >/dev/null 2>&1; then
    echo "install.sh: $python não foi encontrado; a calculadora precisa do CPython 3.12." >&2
    exit 1
fi
if ! "$python" -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))'; then
    echo "install.sh: $python não é o CPython 3.12, a versão homologada." >&2
    exit 1
fi

(cd "$bundle" && sha256sum --check --quiet SHA256SUMS)

set -- "$bundle"/installer/pip-*.whl
installer=$1

"$python" -m venv --without-pip "$target"
"$target/bin/python" "$installer/pip" install \
    --no-index \
    --find-links "$bundle/wheels" \
    --require-hashes \
    --only-binary=:all: \
    --disable-pip-version-check \
    --no-warn-script-location \
    --quiet \
    --requirement "$bundle/requirements.txt"

"$target/bin/qcalc" --version
echo "Instalado em $target, sem acessar a rede."
echo "Para abrir a bancada: $target/bin/qcalc serve"
echo "Para remover o programa: apague $target. O histórico fica na pasta de dados."
