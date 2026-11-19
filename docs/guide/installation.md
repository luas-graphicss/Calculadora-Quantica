# Instalação

A distribuição offline instala a calculadora em uma máquina sem rede. Ela traz o programa, a interface já compilada e todas as dependências como wheels: você não precisa de Node.js, Rust, compilador C nem de serviço remoto.

## Requisitos

Linux x86-64 com glibc 2.27 ou mais nova, CPython 3.12 com o módulo `venv` e o `sha256sum` do coreutils. A plataforma homologada é o Ubuntu 24.04 LTS, onde o Python do sistema é o 3.12 e o módulo `venv` vem no pacote `python3.12-venv`. Esse pacote do sistema é a única coisa que precisa estar na máquina antes; a calculadora não o instala.

Outra versão do Python é recusada pelo instalador, porque não foi homologada. O arquivo tem 62 MiB e a instalação ocupa cerca de 305 MiB.

## Instalar

O pacote é um `.tar.gz` acompanhado do hash. Confira o hash antes de abrir:

    sha256sum --check quantum-calculator-1.0.0rc1-offline-linux_x86_64-cp312.tar.gz.sha256
    tar -xzf quantum-calculator-1.0.0rc1-offline-linux_x86_64-cp312.tar.gz
    cd quantum-calculator-1.0.0rc1-offline-linux_x86_64-cp312
    ./install.sh "$HOME/quantum-calculator"

O instalador confere cada arquivo do pacote contra `SHA256SUMS`, cria um ambiente virtual na pasta indicada e instala os wheels de `wheels/` exigindo o hash de cada um, sem consultar índice de pacotes. Termina assim:

    qcalc 1.0.0rc1
    Instalado em /home/ana/quantum-calculator, sem acessar a rede.
    Para abrir a bancada: /home/ana/quantum-calculator/bin/qcalc serve
    Para remover o programa: apague /home/ana/quantum-calculator. O histórico fica na pasta de dados.

A pasta de destino precisa ser nova: o instalador não escreve por cima de nada. Se o Python 3.12 não se chama `python3.12` na sua máquina, aponte para ele:

    QCALC_PYTHON=/opt/python-3.12/bin/python3 ./install.sh "$HOME/quantum-calculator"

Para chamar `qcalc` sem o caminho, acrescente `$HOME/quantum-calculator/bin` ao `PATH`.

## Conferir a instalação

Na pasta do pacote, o primeiro cálculo:

    "$HOME/quantum-calculator/bin/qcalc" solve reference_cases/quantum/electron_box_1nm.json

A primeira linha deve ser `E = 0.3760301621 eV`. Para repetir nesta máquina todos os casos da homologação e o pacote-testemunha:

    "$HOME/quantum-calculator/bin/python" -m qualification reproduce case_matrix.json reproducao.json --package witness/electron_box_1nm.package.zip

Leva cerca de dois minutos em uma máquina de 2 CPUs. `reproduction.md` explica o que esse comando compara.

## O que vem no pacote

| Caminho | Conteúdo |
| --- | --- |
| `install.sh` | o instalador |
| `wheels/`, `requirements.txt` | a calculadora e as dependências de execução, com o hash de cada wheel |
| `installer/` | o pip usado só para instalar; não entra no ambiente da calculadora |
| `MANIFEST.json`, `SHA256SUMS` | versão, plataforma, pacotes, licenças e o SHA-256 de cada arquivo |
| `licenses/` | `INVENTORY.md`, com cada dependência, versão e licença, e o texto das licenças |
| `docs/` | este guia, a referência da notação e as notas da versão |
| `reference_cases/` | as entradas e os oráculos da homologação |
| `case_matrix.json`, `qualification/` | a matriz de casos e a ferramenta que a reproduz |
| `witness/` | o pacote-testemunha do poço de 1 nm |
| `LICENSE` | GNU GPL versão 3 |

Os casos de `reference_cases/` são dados de teste. Nenhum material de pesquisa acompanha a distribuição.

## Onde ficam os seus dados

O programa fica na pasta que você deu ao instalador. O histórico e os artefatos ficam em outro lugar: `quantum-calculator`, dentro de `$XDG_DATA_HOME` ou, sem essa variável, de `~/.local/share`. `--data-dir` aponta outra pasta em `qcalc serve`, `qcalc backup` e `qcalc restore`.

## Atualizar

Guarde uma cópia do histórico, instale a versão nova em outra pasta e só depois apague a antiga:

    "$HOME/quantum-calculator/bin/qcalc" backup "$HOME/historico-antes-de-atualizar.zip"
    ./install.sh "$HOME/quantum-calculator-1.0.0"

A versão nova abre o mesmo histórico. Se algo der errado, `reproduction.md` mostra como restaurar a cópia em uma pasta vazia.

## Remover

    rm -r "$HOME/quantum-calculator"

Isso remove o programa e mais nada. O histórico fica onde estava, e uma instalação futura volta a abri-lo. Para apagar também a pesquisa, apague você a pasta de dados; nenhum comando da calculadora faz isso.

## Instalar a partir do repositório

Para desenvolver, ou em uma máquina com rede, o `README.md` do repositório mostra o caminho com `uv sync --locked`. A distribuição offline é montada de lá com `python -m distribution build`.
