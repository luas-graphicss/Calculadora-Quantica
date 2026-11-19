# Reprodução

Como entregar um cálculo a outra pessoa, repetir um cálculo recebido, guardar o histórico e conferir uma instalação inteira contra a homologação.

Reproduzir, aqui, é obter as mesmas grandezas e os mesmos veredictos dentro das tolerâncias declaradas. Arquivos binários idênticos não são exigidos: outra máquina tem outra biblioteca de álgebra linear, e os últimos bits de uma resposta numérica mudam com ela.

## Pacote de reprodução

Na bancada, **Exportar pacote** baixa um ZIP da execução:

| Arquivo | Conteúdo |
| --- | --- |
| `manifest.json` | versão do pacote e da calculadora que o gerou, a execução e o tamanho e o SHA-256 de cada arquivo |
| `input.json` | a entrada, byte a byte como foi enviada |
| `problem.json` | o problema canônico, depois da leitura e da conversão de unidades |
| `outcome.json` | o registro com resultado, verificação e ambiente |
| `answers.csv` e tabelas | as respostas e as séries, com a unidade em coluna própria |

O pacote não leva caminho da máquina de origem nem a pasta do usuário. Ele leva a entrada inteira: não exporte o que você não pode divulgar.

Quem recebe usa **Importar pacote**, no histórico. A importação confere cada arquivo contra o manifesto antes de guardar e não calcula nada. A execução aparece como importada, com o aviso "Nada foi recalculado nesta instalação.". Um pacote com um arquivo alterado é recusado inteiro.

"Reexecutar nesta instalação" cria outra execução com a mesma entrada, e a comparação entre as duas mostra, nesta ordem, as versões que diferem, as diferenças na entrada e a razão entre as respostas. Quando o pacote veio de outra versão da calculadora, o título "As execuções usaram versões diferentes" aparece antes das respostas: leia as versões antes de interpretar uma diferença.

`witness/electron_box_1nm.package.zip`, na distribuição, é o pacote do poço de 1 nm exportado pela versão 0.4.0. Importado e reexecutado na 1.0.0rc1, dá razão 1 entre as respostas, com a diferença de versão da calculadora apontada.

Pelo terminal não há comando de pacote. Guardar a saída de `qcalc solve arquivo.json --format json` junto com a entrada dá o mesmo registro, sem o manifesto.

## Comparar duas execuções

Em **Histórico**, marque duas execuções. A comparação lista as versões que diferem, cada campo da entrada que mudou, com os dois valores, e a razão entre as respostas. Sem resposta numérica nas duas, a comparação diz isso em vez de mostrar uma razão.

## Cópia e restauração do histórico

O histórico e os artefatos ficam em `quantum-calculator`, dentro de `$XDG_DATA_HOME` ou de `~/.local/share`, a menos que você use `--data-dir`. Para guardar uma cópia:

    $ qcalc backup ~/copias/historico-2026-11-19.zip
    Cópia gravada em /home/ana/copias/historico-2026-11-19.zip
      execuções: 5
      artefatos: 16, cada um conferido com o próprio hash
      tamanho: 39345 bytes

A cópia é um ZIP com o banco do histórico, os artefatos e um manifesto com o tamanho e o SHA-256 de cada arquivo. Ela é tirada do banco de forma consistente, mesmo com a bancada aberta, e nunca sobrescreve um arquivo que já existe.

Para restaurar, indique uma pasta nova ou vazia:

    $ qcalc restore --data-dir ~/pesquisa-restaurada ~/copias/historico-2026-11-19.zip
    Histórico restaurado em /home/ana/pesquisa-restaurada
      execuções: 5
      artefatos: 16, cada um conferido com o próprio hash
      cópia gravada por esta mesma versão, 1.0.0rc1
      esquema de armazenamento 1, o mesmo desta versão

A restauração não escreve em pasta com conteúdo, para não sobrescrever uma pesquisa. Para voltar a usar o histórico restaurado, abra a bancada nele com `qcalc serve --data-dir ~/pesquisa-restaurada` ou mova a pasta para o lugar padrão.

Um histórico da versão 0.4.0 abre na 1.0.0rc1 sem conversão: o esquema de armazenamento é o mesmo, o 1. Os registros antigos são lidos como foram escritos e não são recalculados.

## Conferir uma instalação contra a homologação

A distribuição traz o corpus (`reference_cases/`), a matriz de casos da homologação (`case_matrix.json`) e a ferramenta que roda um contra o outro. Na pasta da distribuição:

    ~/quantum-calculator/bin/python -m qualification reproduce case_matrix.json reproducao.json --package witness/electron_box_1nm.package.zip

O comando roda os 111 casos pelo `qcalc` instalado, compara cada um com o oráculo e com o que a homologação observou e confere se as fichas instaladas são as homologadas, com as mesmas versões e métodos. Depois abre duas bancadas em pastas temporárias: na primeira importa e reexecuta o pacote-testemunha, e a segunda recebe o pacote exportado dessa reexecução. Não usa rede e não toca no seu histórico. Imprime um resumo, grava o relatório completo em `reproducao.json` e termina com código 0 só quando tudo foi reproduzido:

    Casos reproduzidos: 111 de 111
    Catálogo: as mesmas fichas, versões e métodos
    Pacote electron_box_1nm.package.zip (sha256 4cb6ad3cf658ba06bb6753fd8346ce71faaa4b7e81142eaf70cf72b88480232b): importado como succeeded, reexecução succeeded: reproduzido
      versões diferentes das do pacote: calculadora 0.4.0 -> 1.0.0rc1
      reexecução exportada e importada em outra bancada: succeeded

Um caso que diverge aparece com o nome e a diferença. Cada grandeza é comparada com o oráculo pela tolerância publicada. A ficha escolhida, as respostas em texto, o veredicto, as checagens não aprovadas e as recusas têm de ser iguais aos da homologação.
