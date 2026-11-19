# Limites operacionais

Até onde a versão 1.0.0rc1 vai, quanto ela custa e o que fica fora. Um pedido acima destes limites é recusado antes de calcular, com o campo apontado. Nenhum pedido é reduzido em silêncio.

## Plataforma

Linux x86-64 com CPython 3.12. A plataforma de referência é o Ubuntu 24.04 LTS. Outro sistema, outra arquitetura e outra versão do Python não foram homologados, e o instalador recusa um Python que não seja o 3.12.

A calculadora roda inteira na sua máquina e não abre conexão de rede. A bancada escuta só em `127.0.0.1`.

## Entrada

| O que | Limite |
| --- | --- |
| Documento de entrada | 64 KiB em UTF-8 |
| Literal numérico | 64 caracteres, expoente de módulo até 99 |
| Algarismos significativos pedidos | 34; o padrão é 10 |
| Enunciado | 512 caracteres, 200 nós na árvore, 32 níveis de aninhamento |
| Ordem de derivada no enunciado | 8 |

`NaN` e infinito são recusados. Chaves duplicadas e campos desconhecidos são recusados em vez de ignorados.

## Fichas numéricas

| Ajuste | Limite |
| --- | --- |
| `subintervals` | de 8 a 16384 |
| `levels` | até 32 |
| modos na superposição inicial | até 16 |
| `steps` | até 1 048 576 |
| `samples` | até 100 001 |
| `subdivision_limit` | até 10 000 |
| componentes de um sistema de EDO | até 8 |
| dimensão da base finita | até 16 |

Antes de alocar, a calculadora estima memória e operações a partir de níveis, nós, passos e amostras. Acima de 256 MiB ou de 2e9 operações elementares estimadas, o pedido é recusado com código 7:

    $ qcalc solve reference_cases/numerical/rejected/estimated_work_too_large.json
    Entrada recusada (budget_exceeded)
      /numerics [resource_limit_exceeded]
        O pedido estima 3670592 bytes de memória e 360783806464 operações elementares, acima do perfil homologado. Nada foi alocado.
        esperado: um pedido de até 268435456 bytes e 2000000000 operações estimadas

O limite vale para a estimativa, não para o que o cálculo de fato gastaria: um pedido logo abaixo dele ainda pode esbarrar no limite de tempo.

## Tempo e memória de um cálculo

Cada cálculo simbólico ou numérico roda em um processo separado, com três limites. O tempo de relógio é de 30 s por padrão e vai até 600 s com `--time-limit SEGUNDOS` ou, na bancada, em "Opções avançadas". A memória do processo é fixa em 2048 MiB. O tempo de CPU é o de relógio, arredondado para cima. Passar de um limite encerra o processo, termina com código 7 e não deixa resultado parcial. Cancelar, com Ctrl+C ou pelo botão da bancada, faz o mesmo e termina com código 130.

## Bancada

Uma execução por vez; as outras esperam na fila. O histórico não tem paginação nem exclusão de execução pela interface. Um pacote de reprodução tem até 64 MiB, 64 arquivos e 32 MiB por arquivo. A chave de idempotência de `POST /api/v1/runs` tem de 8 a 128 caracteres.

## Quanto custa

Medido com `python -m benchmarks.harness measure` na versão 1.0.0rc1, em uma máquina com 2 CPUs lógicas Intel Xeon a 2,90 GHz e 3,84 GiB, Amazon Linux 2023, uma thread de álgebra linear, 5 aquecimentos e 30 execuções medidas por carga:

| Carga | Bancada, do envio ao relatório, p50 / p95 | `qcalc solve` em processo novo, p50 | Pico de memória do processo de cálculo |
| --- | --- | --- | --- |
| poço, seis níveis, 4096 subintervalos | 0,400 s / 0,452 s | 1,168 s | 58,6 MiB |
| oscilador, seis níveis, 4096 subintervalos | 0,404 s / 0,472 s | 1,159 s | 58,7 MiB |
| EDO de valor inicial por DOP853 | 0,508 s / 0,556 s | 1,267 s | 76,7 MiB |
| batimento de dois estados por Crank-Nicolson | 0,392 s / 0,420 s | 1,097 s | 56,7 MiB |

A meta da versão é p95 de até 2 s e pico de até 512 MiB para a primeira carga, no perfil de 4 CPUs e 8 GiB. A máquina medida é menor que esse perfil e não é o Ubuntu 24.04, então estes números não são a medição no perfil de referência; servem como cota superior plausível, não como garantia. Quase todo o tempo de uma execução na bancada é criar o processo de cálculo e carregar as bibliotecas: o solver do poço leva 15 ms. Os dados brutos estão em `docs/evidence/phase-5/benchmarks/`, no repositório.

## O que fica fora do escopo

- Potenciais numéricos além do nulo e do harmônico; poço finito, massa efetiva e mais de uma dimensão.
- Hamiltoniano dependente do tempo, estados mistos e medições generalizadas.
- Problemas rígidos: a rigidez não é diagnosticada nem tratada.
- Integrais impróprias, primitivas que pedem funções especiais e EDOs não lineares, de ordem maior ou com coeficientes variáveis em forma fechada.
- Propagação de incerteza experimental nas fichas numéricas, e covariância entre grandezas de entrada.
- Erro da malha espacial na evolução temporal: a ficha mede só o erro no tempo.
- Execuções em paralelo.

Um problema fora do catálogo é recusado com código 4. A calculadora não tenta um método parecido.
