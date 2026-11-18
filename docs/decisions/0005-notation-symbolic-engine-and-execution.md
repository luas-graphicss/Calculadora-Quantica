# 0005 — Notação, motor simbólico e execução com orçamento

Estado: aceita (fase 2). Estende a decisão 0002.

## Contexto

A fase 2 troca a entrada estruturada por um enunciado digitado. Texto do usuário passa a chegar perto do SymPy, um cálculo simbólico pode consumir tempo e memória sem limite, e uma resposta pode valer só sob hipóteses que ninguém declarou.

## Decisão

Gramática própria. `notation` lê texto e um subconjunto de LaTeX com analisadores escritos à mão e produz a árvore tipada de `domain/expressions.py`. A árvore é o que circula entre os pacotes, não o texto nem um objeto do SymPy. Uma leitura com duas interpretações é recusada com o trecho apontado. A referência é `docs/notation/grammar.md`.

Ponte de álgebra. `algebra` é o único lugar que converte a árvore em nós do SymPy, por operações registradas, e que lê o resultado de volta para a árvore. Um resultado que pede operação fora do registro é recusado com `outside_coverage`.

Domínio preservado. As condições de definição saem da expressão original, antes de qualquer simplificação, e acompanham a resposta: exclusões nas variáveis em `validity`, hipóteses sobre parâmetros que o domínio declarado não confirma em `assumptions`. Uma hipótese não confirmada torna a verificação `conditional`.

Três tipos de evidência. Uma identidade é `passed` só quando o resíduo se reduz a zero por simplificação. Um contraexemplo exato reprova como prova. Concordância em pontos amostrados é `numerical_evidence` e deixa a checagem `inconclusive`.

Catálogo versionado. Cada ficha tem versão, área, tipo de problema, domínio e método, e o conjunto tem `CATALOG_VERSION`. A ficha é confirmada na entrada ou sugerida quando só uma é compatível; com mais de uma, a calculadora pede a confirmação.

Processo descartável. O cálculo simbólico roda em um processo filho criado por `spawn`, com `RLIMIT_CPU`, `RLIMIT_AS` e prazo de relógio conferido pelo processo pai. Passar de um limite encerra o filho e vira um diagnóstico `budget_exceeded`; cancelar encerra o filho e termina com código 130. Nenhum estado sobrevive ao processo, então o cálculo seguinte parte limpo. O `pickle` do `multiprocessing` só transporta, entre os dois processos, objetos tipados que o próprio programa criou.

| Pacote | Responsabilidade | Pode importar |
| --- | --- | --- |
| `notation` | Gramáticas, limites de tamanho e escrita da árvore em texto, LaTeX e forma estrutural | `domain` |
| `algebra` | Ponte entre a árvore e o SymPy, análise de domínio e teste de identidade | `domain`, `notation`, SymPy |
| `solvers/symbolic` | Derivação, integração, EDO linear de primeira ordem e leitura da candidata | `domain`, `notation`, `algebra`, SymPy |
| `verification` | Derivação regra a regra, derivada da primitiva e substituição na equação | `domain`, `notation`, `algebra`, SymPy |
| `adapters/execution` | Processo de cálculo com limites e manifesto do ambiente | `domain` |
| `interfaces/serialization` | Documentos de enunciado, de catálogo e de recusa com trecho | `domain`, `notation` |

`method_registry.py` liga cada método do catálogo ao par de solver e verificador; `composition.py` monta o restante.

Regras cobradas por teste:

- `notation` só importa `domain` e a biblioteca padrão. SymPy só aparece em `algebra`, `solvers` e `verification`.
- Nenhum módulo referencia `eval`, `exec`, `sympify` ou `parse_expr`.
- Todo item do corpus rotulado recebe a classificação prevista, pelo validador e pelo CLI.
- Todo método de ficha tem solver e verificador registrados, e o exemplo de cada ficha é resolvido e verificado.
- Um cálculo que passa do orçamento ou é cancelado não deixa processo vivo, e o seguinte roda.

## O que ficou de fora

Métodos numéricos: sem primitiva em forma fechada a integral é recusada, e nenhuma aproximação aparece como alternativa. `adapters/storage`, `interfaces/api` e `web` continuam sem existir.

## Quando rever

Se um problema do catálogo precisar de função especial fora do registro, ou quando a API local da fase 4 tornar caro criar um processo por cálculo.
