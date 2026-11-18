# Calculadora Quântica

Bancada de cálculo para físicos: recebe um problema com parâmetros, unidades e hipóteses explícitas e devolve uma resposta que outra pessoa consegue conferir. "Quântica" descreve a física calculada, não o hardware. Roda em CPU comum, na sua máquina.

O que existe hoje é a fase 1 do roadmap: um problema, de ponta a ponta, pelo CLI. A energia de uma partícula em um poço infinito unidimensional sai com expressão, valor, unidade, constantes, hipóteses, memória de cálculo e verificação.

## Requisitos

Linux x86-64, CPython 3.12 e [uv](https://docs.astral.sh/uv/) 0.13.5. A plataforma de referência é Ubuntu 24.04 LTS; outras não foram homologadas.

## Como rodar

    git clone https://github.com/luas-graphicss/Calculadora-Quantica.git
    cd Calculadora-Quantica
    uv sync --locked
    uv run qcalc validate reference_cases/quantum/electron_box_1nm.json
    uv run qcalc solve reference_cases/quantum/electron_box_1nm.json

`validate` mostra como a entrada foi entendida e o plano de cálculo, sem calcular. `solve` responde na primeira linha:

    E = 0.3760301621 eV
    resultado exact; 10 algarismos significativos, arredondamento half_even; verificação: passed

Depois vêm as hipóteses, os parâmetros convertidos para o SI, as constantes com edição e fonte, a memória de cálculo, a incerteza, a verificação, as limitações e o ambiente. Com `--format json` o mesmo conteúdo sai como um registro versionado; a saída completa do caso acima está em `docs/evidence/phase-1/`.

## A entrada

```json
{
  "schema_version": "1.0",
  "problem": "quantum.infinite_square_well.energy_level",
  "hypotheses": {
    "walls": "infinite",
    "interior_potential": "zero",
    "boundary_wavefunction": "zero"
  },
  "parameters": {
    "mass": {"constant": "electron_mass"},
    "width": {"value": 1, "unit": "nm"},
    "level": 1
  },
  "requested": {"quantity": "energy", "unit": "eV", "significant_digits": 10}
}
```

Nada é presumido. As três hipóteses precisam estar escritas, a massa é um valor com unidade ou uma constante do catálogo citada pelo nome, e a unidade de exibição é pedida. Números aceitam inteiros, decimais e frações como `"1/3"`, e ficam exatos até a exibição.

Para propagar incertezas, declare a hipótese de covariância e a incerteza-padrão de cada grandeza:

```json
"uncertainty": {
  "covariance": "independent",
  "standard_uncertainties": {
    "mass": {"value": "2.8e-40", "unit": "kg"},
    "width": {"value": "0.01", "unit": "nm"}
  }
}
```

Sem esse bloco o resultado traz "incerteza não avaliada", nunca zero. O esquema completo sai com `uv run qcalc schema problem`; o da saída, com `uv run qcalc schema output`.

## Quando a entrada é recusada

Uma largura em segundos termina com código 3, nada na saída padrão e este diagnóstico na saída de erro:

    Entrada recusada (invalid_input)
      /parameters/width/unit [dimension_mismatch]
        A unidade "s" mede tempo, mas o parâmetro width (largura do poço) exige comprimento.
        esperado: unidade de comprimento: m, mm, μm, nm, Å, pm

| Código | Significado |
| --- | --- |
| 0 | Concluído; em `solve`, verificação `passed` |
| 1 | O arquivo de entrada não pôde ser lido |
| 2 | Uso incorreto da linha de comando |
| 3 | `invalid_input`: a entrada tem defeito |
| 4 | `unsupported_problem`: o problema é outro, fora do catálogo |
| 5 | Resultado calculado, mas a verificação não passou |

## Estrutura

    src/quantum_calculator/
      domain/         dimensões, grandezas exatas, contratos e arredondamento; só biblioteca padrão
      catalog/        fichas de problemas homologados
      application/    validação guiada pela ficha, plano e execução
      solvers/        solução fechada com SymPy
      verification/   verificador independente do solver
      adapters/       registro de unidades, constantes CODATA 2022 e manifesto de ambiente
      interfaces/     leitura e escrita dos documentos JSON, esquemas e CLI
    reference_cases/  entradas, oráculos e derivações independentes
    docs/decisions/   decisões de plataforma, fronteiras, convenções físicas e arredondamento
    docs/evidence/    saída real do CLI que encerra cada fase

## Desenvolvimento

    uv run ruff format --check .
    uv run ruff check .
    uv run mypy
    uv run pytest

As identidades exatas e as comparações numéricas com tolerância rodam separadas: `uv run pytest -m algebraic` e `uv run pytest -m numerical`.

## Status

Funciona: o caso do poço infinito pelo CLI, com unidades, constantes CODATA 2022, propagação linear de incertezas independentes e verificação por substituição na equação de Schrödinger.

Não existe ainda: leitura de equações digitadas, outros problemas do catálogo, solvers numéricos, API local e interface web. São as fases 2 a 5 do roadmap.

Limites conhecidos: as mensagens de uso geradas pelo `argparse` estão em inglês, e a evidência registrada em `docs/evidence/phase-1/` foi gerada fora da plataforma de referência; a CI a reproduz em Ubuntu 24.04.

## Licença

GNU GPL versão 3. Veja `LICENSE`.
