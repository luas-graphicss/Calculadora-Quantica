# Evidência de encerramento da fase 1

Saída real do CLI para o caso testemunha, gerada de uma instalação limpa: wheel construído do repositório e instalado em um ambiente virtual novo, só com as dependências de execução do `uv.lock`.

| Evidência pedida pelo roadmap | Onde está |
| --- | --- |
| Entrada testemunha | `reference_cases/quantum/electron_box_1nm.json` |
| Derivação independente | `reference_cases/quantum/electron_box_1nm.derivation.md` |
| Saída real do CLI | `electron_box_1nm.validate.txt`, `electron_box_1nm.solve.txt` e `electron_box_1nm.run_record.json` |
| Manifesto de ambiente | campo `environment` de `electron_box_1nm.run_record.json` |
| Esquema | `src/quantum_calculator/interfaces/serialization/schemas/`, ou `qcalc schema problem` e `qcalc schema output` |
| Relatório da CI | workflow `CI` em `.github/workflows/ci.yml`; o job de instalação limpa publica o artefato `phase-1-reproduction` |

Também ficam aqui o registro com incertezas independentes (`electron_box_1nm_uncertainty.run_record.json`) e um exemplo de recusa (`width_in_seconds.rejection.json`): é a saída de erro para uma largura dada em segundos, com o processo terminando em código 3 e nada na saída padrão.

## Como foi gerada

    uv build --wheel --out-dir dist
    uv export --locked --no-dev --no-emit-project --output-file runtime-requirements.txt
    uv venv --python 3.12 clean-environment
    uv pip install --python clean-environment/bin/python --require-hashes --requirement runtime-requirements.txt
    uv pip install --python clean-environment/bin/python --no-deps dist/*.whl
    clean-environment/bin/qcalc validate reference_cases/quantum/electron_box_1nm.json
    clean-environment/bin/qcalc solve reference_cases/quantum/electron_box_1nm.json
    clean-environment/bin/qcalc solve reference_cases/quantum/electron_box_1nm.json --format json

## Limite desta evidência

Os arquivos foram gerados em Amazon Linux 2023 (kernel 6.18, glibc 2.34) com CPython 3.12.15, como o manifesto registra, e não na plataforma de referência. A CI repete os mesmos passos em Ubuntu 24.04 e compara o registro JSON com o daqui, ignorando só o campo `environment`. O teste `tests/contracts/test_recorded_evidence.py` faz a mesma comparação a cada execução da suíte: mudar a saída sem regenerar estes arquivos quebra o build.

Os arquivos foram regenerados nas fases 2 e 3, quando o esquema de saída passou a 1.1 e depois a 1.2; o conteúdo científico do caso não mudou.

## Critérios de aceite

- Uma instalação limpa reproduz o caso com expressão, valor, unidade, constantes e hipóteses: campos `result`, `constants` e `problem.hypotheses` de `electron_box_1nm.run_record.json`.
- Equivalência e escala: `tests/unit/solvers/test_infinite_square_well_identities.py` cobre 1 nm contra 10 Å, largura dobrada e segundo nível. Entradas inválidas: `reference_cases/quantum/rejected/`, conferidas por `tests/integration/test_cli_rejections.py`.
- Núcleo testável sem navegador, servidor HTTP, banco de dados ou módulo nativo: a suíte roda inteira com `uv run pytest`, e `tests/contracts/test_dependency_direction.py` impede que o domínio importe qualquer biblioteca.

Ainda não há alegação de solver geral de Schrödinger.
