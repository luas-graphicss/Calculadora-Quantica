# Medição de desempenho

Mede quanto tempo a calculadora leva, e quanta memória o processo de cálculo ocupa, nas quatro cargas da homologação: o poço, o oscilador, uma EDO e uma propagação temporal. Cada resposta medida é comparada com um oráculo, e a medição para se uma delas sair da tolerância.

    uv run python -m benchmarks.harness measure medicao.json

O comando grava os dados brutos em `medicao.json`, imprime o resumo e termina com código 1 se uma meta não for atingida. Para comparar duas medições, carga a carga:

    uv run python -m benchmarks.harness compare docs/evidence/phase-5/benchmarks/baseline.json medicao.json

## O que está congelado

`reference_profile.json` fixa a máquina de referência (4 CPUs lógicas x86-64, 8 GiB, Ubuntu 24.04, CPython 3.12), uma execução por vez, uma thread de álgebra linear, nenhum cache de resultados, cinco execuções frias, cinco aquecimentos e 30 execuções medidas. A meta é a do roadmap: seis níveis do poço em 4096 subintervalos, com p95 até 2 s do envio ao relatório e pico de RSS do worker até 512 MiB.

`workloads/index.json` lista as cargas, o oráculo de cada resposta e a tolerância com o motivo. Lista também um pedido acima do perfil homologado, que precisa ser recusado com código 7 antes de alocar.

Mudar um desses arquivos muda a pergunta que a medição responde. Uma tolerância só muda com justificativa científica, escrita no campo `oracle`.

## Como cada tempo é medido

| Percurso | O que roda | O que o tempo cobre |
| --- | --- | --- |
| frio | `qcalc solve arquivo --format json` em processo novo | da chamada ao registro impresso, com a carga do interpretador e das bibliotecas |
| quente | um `qcalc serve` já em pé, pela API local | do `POST /api/v1/runs` ao `GET /api/v1/runs/{id}` que devolve o registro concluído, com fila, processo de cálculo e gravação no histórico |
| estágios | os mesmos casos de uso, no processo da medição | interpretação, preparação, solver, verificação e serialização, cada um à parte |

Interpretação é ler o documento e validá-lo contra a ficha. Preparação é o que o processo de cálculo custa fora do cálculo: criar o processo, carregar os módulos, aplicar os limites e transferir o problema e o desfecho. Solver e verificação são cronometrados dentro do processo de cálculo. Serialização é montar o registro e escrevê-lo em JSON.

Cada envio à bancada usa uma chave de idempotência nova, então nenhum resultado é reaproveitado. O percentil é o do posto mais próximo: com 30 execuções, o p95 é a 29ª em ordem crescente.

O pico de memória do worker sai de duas leituras. Na bancada, o `VmHWM` do processo de cálculo em `/proc`, lido a cada consulta enquanto ele existe. No percurso por estágios, o `VmHWM` que o próprio processo lê ao terminar; o `ru_maxrss` não serve, porque depois de um `fork` ele também conta o tamanho do processo pai. A meta usa a maior das duas leituras.

## Limites

A medição só vale para o perfil de referência quando o resumo diz que a máquina corresponde a ele. Fora dele, os dados servem para comparar duas versões na mesma máquina.

O percurso por estágios mede fichas numéricas. A leitura da memória na bancada precisa de `/proc/<pid>/task/<tid>/children`, que existe em Linux com `CONFIG_PROC_CHILDREN`.
