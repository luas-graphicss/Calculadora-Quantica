# 0004 — Arredondamento e representação de resultados

Estado: aceita (fase 1).

## Aritmética

Inteiros e racionais ficam exatos até a saída. Literais decimais como `1e-9` viram frações exatas; `1/3` é aceito como texto. Nenhum ponto flutuante binário participa do cálculo nesta fase, então não há erro de arredondamento antes da exibição.

## Arredondamento decimal

- O valor exibido é a fração exata arredondada para N algarismos significativos, metade para o par (`half_even`), com a divisão corretamente arredondada do módulo `decimal`.
- N vem de `requested.significant_digits`; o padrão é 10 e o máximo é 34. O plano de cálculo registra o N usado.
- Cada número exato sai com quatro campos: `decimal`, `is_exact`, `numerator` e `denominator`. `is_exact` diz se `decimal` representa o racional sem perda. Zeros à direita não são acrescentados para completar N.
- Parâmetros, constantes e passos intermediários são exibidos com até 34 algarismos, para que a conferência manual não dependa do N pedido para a resposta.
- Incertezas-padrão saem com 2 algarismos significativos. A raiz quadrada é calculada com 25 dígitos de guarda antes do arredondamento final.

## Formato

- Todo número, no texto e no JSON, usa ponto decimal e notação científica com `E`, para poder ser colado em outra ferramenta. No JSON os valores físicos são strings, nunca `float`, porque um leitor JSON os converteria para binário.
- O JSON de saída declara `document` (`validation`, `run_record` ou `rejection`) e `schema_version` (`1.0`). Os esquemas ficam em `src/quantum_calculator/interfaces/serialization/schemas/` e saem por `qcalc schema`.
- A saída não tem data nem hora. A mesma entrada no mesmo ambiente gera a mesma saída byte a byte.
- A primeira linha do texto responde à pergunta. Hipóteses, memória de cálculo, verificação, incerteza e limitações vêm depois.

## Vocabulário

- Natureza do resultado: `exact` ou `approximate`.
- Verificação: `passed`, `conditional`, `inconclusive` ou `failed`. A execução ter terminado não é aprovação científica.
- Recusa: `invalid_input` ou `unsupported_problem`, com `code`, `pointer` (JSON Pointer do campo), mensagem e a unidade ou restrição esperada.

## Códigos de saída do CLI

| Código | Significado |
| --- | --- |
| 0 | Concluído; em `solve`, verificação `passed` |
| 1 | O arquivo de entrada não pôde ser lido |
| 2 | Uso incorreto da linha de comando |
| 3 | `invalid_input` |
| 4 | `unsupported_problem` |
| 5 | Resultado calculado, mas a verificação não passou |

Em caso de recusa nada é escrito na saída padrão; o diagnóstico vai para a saída de erro, no formato pedido.

## Limites da entrada

Documento de até 64 KiB em UTF-8; literais numéricos de até 64 caracteres com expoente de módulo até 999; `NaN` e infinitos são recusados, como token JSON ou como texto. Chaves duplicadas e campos desconhecidos são recusados em vez de ignorados.

## Quando rever

Quando existir caminho numérico em dupla precisão (fase 3) ou saída com amostras e séries.
