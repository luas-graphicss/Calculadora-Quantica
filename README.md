# Calculadora Quântica

Bancada de cálculo para físicos: recebe um problema com parâmetros, unidades e hipóteses explícitas e devolve uma resposta que outra pessoa consegue conferir. "Quântica" descreve a física calculada, não o hardware. Roda em CPU comum, na sua máquina.

O que existe hoje são as fases 1 e 2 do roadmap, pelo CLI. A fase 1 resolve a energia de uma partícula em um poço infinito unidimensional, com expressão, valor, unidade, constantes, hipóteses, memória de cálculo e verificação. A fase 2 lê um enunciado digitado em texto ou LaTeX, mostra de volta o que entendeu e deriva, integra, resolve uma EDO linear de primeira ordem ou revisa uma solução candidata.

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

## Problema por ficha

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

Sem esse bloco o resultado traz "incerteza não avaliada", nunca zero.

## Enunciado digitado

```json
{
  "schema_version": "1.0",
  "problem": "ode.first_order_linear.initial_value",
  "notation": "text",
  "statement": "y' = -k*y",
  "symbols": {
    "t": {"role": "variable", "domain": "real", "unit": "s"},
    "k": {"role": "parameter", "domain": "positive", "unit": "1/s"},
    "y_0": {"role": "parameter", "domain": "positive", "unit": "1"},
    "y": {"role": "function", "domain": "real", "unit": "1", "argument": "t"}
  },
  "conditions": ["y(0) = y_0"]
}
```

O enunciado vai em texto (`diff(x^2*sin(x), x)`, `integral(1/x, x)`) ou em um subconjunto de LaTeX (`\int_{0}^{1} x^{2} \, dx`); a referência está em `docs/notation/grammar.md`. Todo símbolo é declarado com papel, domínio e unidade. `problem` confirma a ficha: sem ele, a calculadora sugere a ficha quando só uma é compatível e pede a confirmação quando há mais de uma.

    uv run qcalc validate reference_cases/symbolic/decay_initial_value.json
    uv run qcalc solve reference_cases/symbolic/decay_initial_value.json

`validate` devolve a leitura em três formas, para conferir antes de calcular:

    Leitura
      texto: y'(t) = -k*y(t)
      LaTeX: y'(t) = -k \cdot y(t)
      árvore: (equation (unknown y 1 (symbol t)) (negate (multiply (symbol k) (unknown y 0 (symbol t)))))
      entrada (text): y' = -k*y

`solve` responde na primeira linha e lista abaixo onde a resposta vale, as hipóteses que o domínio declarado não confirma, os casos especiais e as constantes arbitrárias:

    y(t) = y_0*exp(-k*t)
    resultado exact; adimensional; verificação: passed

Para revisar uma solução, use a ficha `ode.first_order_linear.candidate_review` e o campo `candidate`. A candidata é substituída na equação e a condição inicial é conferida à parte, então os dois motivos de reprovação saem separados:

    $ uv run qcalc solve reference_cases/symbolic/decay_candidate_wrong_initial_value.json
    Candidata reprovada: y(t) = 2*y_0*exp(-k*t)
    revisão por substituição; adimensional; verificação: failed (initial_condition)

Uma identidade que a simplificação não demonstra fica `inconclusive`: concordância em pontos amostrados é relatada como evidência numérica, nunca como prova.

O cálculo simbólico roda em um processo separado, com limite de CPU, de memória e de tempo de relógio. `--time-limit SEGUNDOS` muda o tempo de relógio (padrão 30, máximo 600). Passar do limite ou cancelar com Ctrl+C encerra esse processo e não deixa resultado parcial.

`uv run qcalc catalog` lista as fichas homologadas com versão, área, tipo, domínio, método e limitações. Os esquemas saem com `uv run qcalc schema problem`, `schema statement` e `schema output`.

## Quando a entrada é recusada

Uma largura em segundos termina com código 3, nada na saída padrão e este diagnóstico na saída de erro:

    Entrada recusada (invalid_input)
      /parameters/width/unit [dimension_mismatch]
        A unidade "s" mede tempo, mas o parâmetro width (largura do poço) exige comprimento.
        esperado: unidade de comprimento: m, mm, μm, nm, Å, pm

Um enunciado com duas leituras termina com código 6 e o trecho marcado. Nada é corrigido em silêncio:

    Entrada recusada (ambiguous_input)
      /statement [ambiguous_division]
        Depois de uma divisão, outro fator na mesma sequência admite duas leituras.
        esperado: parênteses que fixem a leitura, como (a/b)*c ou a/(b*c)
        trecho: diff(1/2x, x)
                     ^^^^

| Código | Significado |
| --- | --- |
| 0 | Concluído; em `solve`, verificação `passed` |
| 1 | O arquivo de entrada não pôde ser lido |
| 2 | Uso incorreto da linha de comando |
| 3 | `invalid_input`: a entrada tem defeito |
| 4 | `unsupported_problem`: o problema é outro, fora do catálogo |
| 5 | Resultado calculado, mas a verificação não passou (`failed`, `conditional` ou `inconclusive`) |
| 6 | `ambiguous_input`: o enunciado ou a escolha da ficha admite mais de uma leitura |
| 7 | `budget_exceeded`: o enunciado ou o cálculo passou de um limite |
| 8 | O processo de cálculo terminou sem devolver resultado |
| 130 | Cálculo cancelado |

## Estrutura

    src/quantum_calculator/
      domain/         dimensões, grandezas exatas, árvore de expressão, contratos e diagnósticos; só biblioteca padrão
      notation/       gramática de texto e de LaTeX, e a escrita da árvore de volta nas três formas
      catalog/        fichas homologadas e a versão do catálogo
      application/    validação guiada pela ficha, plano, orçamento e casos de uso
      algebra/        ponte entre a árvore e o SymPy, análise de domínio e teste de identidade
      solvers/        soluções fechadas e operações simbólicas
      verification/   verificadores independentes dos solvers
      adapters/       unidades, constantes CODATA 2022, manifesto de ambiente e processo de cálculo
      interfaces/     leitura e escrita dos documentos JSON, esquemas e CLI
    reference_cases/  entradas, oráculos, derivações independentes e o corpus da notação
    docs/decisions/   decisões de plataforma, fronteiras, convenções físicas, arredondamento e notação
    docs/notation/    referência da gramática
    docs/evidence/    saída real do CLI que encerra cada fase

## Desenvolvimento

    uv run ruff format --check .
    uv run ruff check .
    uv run mypy
    uv run pytest

As identidades exatas e as comparações numéricas com tolerância rodam separadas: `uv run pytest -m algebraic` e `uv run pytest -m numerical`.

## Status

Funciona: o poço infinito, com unidades, constantes CODATA 2022 e propagação linear de incertezas independentes; e, a partir de um enunciado digitado, derivada ordinária ou parcial, primitiva, integral definida em intervalo sem singularidade, EDO linear escalar de primeira ordem com coeficientes constantes e revisão de candidata.

Não existe ainda: solvers numéricos, API local e interface web. São as fases 3 a 5 do roadmap. Sem primitiva em forma fechada, a integral é recusada; nenhuma aproximação numérica é oferecida.

Limites conhecidos: as mensagens de uso geradas pelo `argparse` estão em inglês; o limite de memória do processo de cálculo é fixo em 2048 MiB; e a evidência registrada em `docs/evidence/` foi gerada fora da plataforma de referência, com a CI a reproduzindo em Ubuntu 24.04.

## Licença

GNU GPL versão 3. Veja `LICENSE`.
