# Evidência de encerramento da fase 2

Saída real do CLI para os enunciados digitados, gerada de uma instalação limpa: wheel construído do repositório e instalado em um ambiente virtual novo, só com as dependências de execução do `uv.lock`.

| Evidência pedida pelo roadmap | Onde está |
| --- | --- |
| Referência da gramática | `docs/notation/grammar.md` |
| Catálogo versionado | `catalog.txt` e `catalog.json`, saída de `qcalc catalog` |
| Corpus de aceitação e recusa | `reference_cases/notation/corpus.json`: 54 itens rotulados à mão, com leitura pretendida e motivo de recusa |
| Relatório da suíte | `suite_report.txt`; na CI, o artefato `test-reports` traz o JUnit de cada etapa |
| Revisão da EDO com a condição inicial incorreta | `decay_candidate_wrong_initial_value.solve.txt` e `decay_candidate_wrong_initial_value.run_record.json` |

Também ficam aqui a prévia de um enunciado (`product_rule.validate.txt`), um problema de valor inicial resolvido (`decay_initial_value.solve.txt` e `.run_record.json`), a candidata com o sinal trocado (`decay_candidate_wrong_sign.solve.txt`), a recusa de uma divisão ambígua com o trecho marcado (`ambiguous_division.rejection.txt` e `.json`) e a recusa por limite de tempo (`time_budget_exceeded.rejection.txt`).

Os dois motivos de reprovação saem em linhas diferentes. Valor inicial errado:

    Candidata reprovada: y(t) = 2*y_0*exp(-k*t)
    revisão por substituição; adimensional; verificação: failed (initial_condition)

Sinal errado:

    Candidata reprovada: y(t) = y_0*exp(k*t)
    revisão por substituição; adimensional; verificação: failed (equation_residual)

## Como foi gerada

    uv build --wheel --out-dir dist
    uv export --locked --no-dev --no-emit-project --output-file runtime-requirements.txt
    uv venv --python 3.12 clean-environment
    uv pip install --python clean-environment/bin/python --require-hashes --requirement runtime-requirements.txt
    uv pip install --python clean-environment/bin/python --no-deps dist/*.whl
    clean-environment/bin/qcalc catalog
    clean-environment/bin/qcalc catalog --format json
    clean-environment/bin/qcalc validate reference_cases/symbolic/product_rule.json
    clean-environment/bin/qcalc solve reference_cases/symbolic/decay_initial_value.json
    clean-environment/bin/qcalc solve reference_cases/symbolic/decay_initial_value.json --format json
    clean-environment/bin/qcalc solve reference_cases/symbolic/decay_candidate_wrong_initial_value.json
    clean-environment/bin/qcalc solve reference_cases/symbolic/decay_candidate_wrong_initial_value.json --format json
    clean-environment/bin/qcalc solve reference_cases/symbolic/decay_candidate_wrong_sign.json
    clean-environment/bin/qcalc solve reference_cases/symbolic/rejected/ambiguous_division.json
    clean-environment/bin/qcalc solve reference_cases/symbolic/rejected/ambiguous_division.json --format json
    clean-environment/bin/qcalc solve reference_cases/symbolic/product_rule.json --time-limit 0.05

As duas revisões reprovadas terminam com código 5, a divisão ambígua com 6 e o limite de tempo com 7. Nas recusas o arquivo guarda a saída de erro; a saída padrão fica vazia.

## Limite desta evidência

Os arquivos foram gerados em Amazon Linux 2023 (kernel 6.18, glibc 2.34) com CPython 3.12.15, como o manifesto registra, e não na plataforma de referência. A CI repete a geração em Ubuntu 24.04 e compara o catálogo, a prévia e os dois registros JSON com os daqui, ignorando só o campo `environment`. `tests/contracts/test_recorded_symbolic_evidence.py` compara todos os arquivos a cada execução da suíte, menos `suite_report.txt`, que é o retrato da execução que fechou a fase: os tempos e as contagens dele mudam com a máquina e com a suíte.

A saída mudou de formato nesta fase: o esquema de saída passou a 1.1, com os documentos de enunciado e de catálogo e o campo `excerpt` nas recusas. Por isso a evidência da fase 1 foi regenerada pelo mesmo procedimento.

## Critérios de aceite

- Todo item do corpus recebe a classificação prevista. `tests/contracts/test_notation_corpus.py` confere classificação, árvore, ficha, código, campo e trecho pelo validador; `tests/integration/test_cli_statement_refusals.py` confere a classificação e o código de saída pelo CLI.
- O CLI resolve e revisa os exemplos declarados. `reference_cases/symbolic/expectations.json` traz a resposta derivada à mão de cada exemplo, e `tests/integration/test_cli_statements.py` a compara por equivalência com a saída, junto com o veredito, as exclusões de domínio e as constantes arbitrárias. Nenhuma checagem passa com evidência numérica: `tests/unit/verification/test_candidate_review.py` mostra que concordância só em pontos amostrados deixa a revisão `inconclusive`.
- Cancelamento e excesso de orçamento deixam o cálculo seguinte utilizável: `tests/unit/adapters/test_process_executor.py`, `tests/unit/application/test_solve_statement.py` e, com um SIGINT de verdade no grupo do processo, `tests/e2e/test_module_entry_point.py`.
- A entrada nunca é executada como programa: `tests/contracts/test_dependency_direction.py` recusa qualquer referência a `eval`, `exec`, `sympify` ou `parse_expr` e mantém o SymPy fora de `domain` e `notation`.

Nenhum método numérico foi homologado nesta fase. Uma integral sem primitiva em forma fechada é recusada, sem alternativa aproximada.
