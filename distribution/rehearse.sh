#!/bin/sh
set -eu

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "uso: rehearse.sh ARQUIVO.tar.gz PASTA_DE_TRABALHO [HISTORICO_ANTERIOR]" >&2
    exit 2
fi

archive_directory=$(CDPATH='' cd -- "$(dirname -- "$1")" && pwd)
archive_name=$(basename -- "$1")
work=$2
earlier_history=${3:-}

if [ -e "$work" ]; then
    echo "rehearse.sh: $work já existe; escolha uma pasta nova." >&2
    exit 1
fi
mkdir -p "$work"
work=$(CDPATH='' cd -- "$work" && pwd)
bundle="$work/$(basename -- "$archive_name" .tar.gz)"
program="$work/program"

step() {
    printf '\n== %s\n' "$1"
}

listing() {
    (cd "$1" && find . -type f -exec sha256sum {} + | sort -k 2)
}

same_listing() {
    test "$(sha256sum < "$1")" = "$(sha256sum < "$2")"
}

step "O arquivo confere com o hash publicado"
(cd "$archive_directory" && sha256sum --check "$archive_name.sha256")

step "Instalação a partir do pacote"
tar -xzf "$archive_directory/$archive_name" -C "$work"
"$bundle/install.sh" "$program"

step "Primeiro cálculo"
(cd "$bundle" && "$program/bin/qcalc" solve reference_cases/quantum/electron_box_1nm.json) > "$work/first_calculation.txt"
head -n 2 "$work/first_calculation.txt"

step "Corpus da homologação e pacote-testemunha"
(cd "$bundle" && "$program/bin/python" -m qualification reproduce case_matrix.json \
    "$work/reproduction.json" --package witness/electron_box_1nm.package.zip) | tee "$work/reproduction.txt"

if [ -z "$earlier_history" ]; then
    exit 0
fi

step "Histórico anterior em cópia isolada"
mkdir "$work/research"
cp -R "$earlier_history/history.sqlite3" "$earlier_history/artifacts" "$work/research/"
listing "$work/research" > "$work/research.before"
"$program/bin/qcalc" backup --data-dir "$work/research" "$work/history.zip"

step "Remoção do programa"
rm -r "$program"
listing "$work/research" > "$work/research.after"
if ! same_listing "$work/research.before" "$work/research.after"; then
    echo "rehearse.sh: a pasta da pesquisa mudou depois de abrir o histórico e remover o programa." >&2
    exit 1
fi
echo "Programa removido; os $(wc -l < "$work/research.after") arquivos da pesquisa continuam iguais."

step "Reinstalação e restauração em pasta vazia"
"$bundle/install.sh" "$program"
"$program/bin/qcalc" restore --data-dir "$work/restored" "$work/history.zip"
listing "$work/research/artifacts" > "$work/artifacts.original"
listing "$work/restored/artifacts" > "$work/artifacts.restored"
if ! same_listing "$work/artifacts.original" "$work/artifacts.restored"; then
    echo "rehearse.sh: os artefatos restaurados diferem dos originais." >&2
    exit 1
fi
echo "Os $(wc -l < "$work/artifacts.restored") artefatos restaurados são os originais, byte a byte."
