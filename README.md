# Calculadora Quântica

Bancada de cálculo para físicos: recebe um problema com parâmetros, unidades e hipóteses explícitas e devolve uma resposta que outra pessoa consegue conferir. "Quântica" descreve a física calculada, não o hardware. Roda em CPU comum, na sua máquina.

O que existe hoje são as fases 1 a 3 do roadmap, pelo CLI. A fase 1 resolve a energia de uma partícula em um poço infinito unidimensional, com expressão, valor, unidade, constantes, hipóteses, memória de cálculo e verificação. A fase 2 lê um enunciado digitado em texto ou LaTeX, mostra de volta o que entendeu e deriva, integra, resolve uma EDO linear de primeira ordem ou revisa uma solução candidata. A fase 3 aproxima integrais, trajetórias, medições em base finita, espectros e evoluções de Schrödinger em uma dimensão, com o erro de cada resposta caracterizado.

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

## Problema numérico

```json
{
  "schema_version": "1.0",
  "problem": "quantum.infinite_square_well.discrete_spectrum",
  "hypotheses": {
    "walls": "infinite",
    "interior_potential": "zero",
    "boundary_wavefunction": "zero"
  },
  "parameters": {
    "mass": {"constant": "electron_mass"},
    "width": {"value": 1, "unit": "nm"}
  },
  "numerics": {"subintervals": 512, "levels": 3},
  "requested": {"unit": "eV", "significant_digits": 10}
}
```

Uma ficha numérica devolve uma resposta aproximada, então a resolução vem escrita em `numerics`: malha, passos e tolerâncias. Sem esse bloco a entrada é recusada; nenhuma resolução é escolhida em silêncio.

| Ficha | O que calcula | Ajustes em `numerics` |
| --- | --- | --- |
| `calculus.definite_integral.adaptive_quadrature` | integral definida, por quadratura adaptativa | `absolute_tolerance`, `relative_tolerance`, `subdivision_limit` |
| `ode.initial_value.explicit_runge_kutta` | trajetória de um sistema explícito não rígido, por DOP853 | `end`, `samples`, `relative_tolerance`, `absolute_tolerance` |
| `quantum.finite_basis.projective_measurement` | probabilidades e valor esperado de um observável em base finita | `tolerance` |
| `quantum.infinite_square_well.discrete_spectrum` | níveis e autofunções do poço, por diferenças finitas | `subintervals`, `levels` |
| `quantum.harmonic_oscillator.truncated_spectrum` | níveis e autofunções do oscilador em domínio truncado | `subintervals`, `levels`, `half_width` |
| `quantum.infinite_square_well.time_evolution` | evolução de uma superposição, por Crank-Nicolson | `subintervals`, `steps`, `samples` |

    uv run qcalc validate reference_cases/numerical/electron_box_1nm_discrete.json
    uv run qcalc solve reference_cases/numerical/electron_box_1nm_discrete.json

`validate` mostra a leitura, a resolução pedida e a estimativa de memória e de trabalho, sem calcular. `solve` responde com cada grandeza, a unidade e o erro estimado:

    E_1 = 0.3760289823 eV; erro estimado 0.0000012 eV (erro de malha estimado por extrapolação de Richardson entre 256 e 512 subintervalos)
    E_2 = 1.504101772 eV; erro estimado 0.000019 eV (erro de malha estimado por extrapolação de Richardson entre 256 e 512 subintervalos)
    E_3 = 3.384175898 eV; erro estimado 0.000096 eV (erro de malha estimado por extrapolação de Richardson entre 256 e 512 subintervalos)
    resultado approximate; 10 algarismos significativos, arredondamento half_even; verificação: passed

Abaixo vêm os parâmetros efetivos do método, as tabelas e a verificação. Três fontes de erro saem em checagens separadas: `discrete_residual` confere o operador discreto, `mesh_refinement` mede a discretização repetindo o cálculo com um quarto e com a metade da malha, e `domain_truncation` amplia o domínio do oscilador com o mesmo espaçamento. Um resíduo pequeno não aprova a malha. Com 16 subintervalos o mesmo poço termina com código 5:

    $ uv run qcalc solve reference_cases/numerical/electron_box_1nm_coarse.json
    inconclusive [numerical_evidence] mesh_refinement
      observado: ordem observada entre 1.746 e 1.972 com 4, 8 e 16 subintervalos: a malha não está no regime assintótico e não é declarada convergida

A integral e a trajetória usam a notação do enunciado digitado, com um valor para cada parâmetro, como `"k": {"role": "parameter", "domain": "positive", "unit": "1/s", "value": 1}`. O estado e o observável de base finita entram como listas; uma amplitude complexa é `{"real": 0, "imaginary": 1}`, e `"normalize": true` pede a normalização, que fica registrada no resultado. Com `--format json` as tabelas saem completas; em texto, as longas são amostradas.

Antes de alocar, a calculadora estima memória e operações a partir de níveis, nós, passos e amostras, e recusa com código 7 o pedido acima do perfil homologado. Um método que não converge termina com código 9, sem resposta aprovada. O cálculo numérico roda no mesmo processo separado, com os mesmos limites e o mesmo `--time-limit`.

`uv run qcalc catalog` lista as fichas homologadas com versão, área, tipo, domínio, método e limitações. Os esquemas saem com `uv run qcalc schema problem`, `schema statement`, `schema numerical` e `schema output`.

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
| 7 | `budget_exceeded`: o enunciado, o pedido ou o cálculo passou de um limite |
| 8 | O processo de cálculo terminou sem devolver resultado |
| 9 | `non_convergent`: o método numérico não convergiu ou deu valor não finito |
| 130 | Cálculo cancelado |

## Estrutura

    src/quantum_calculator/
      domain/         dimensões, grandezas exatas, árvore de expressão, contratos e diagnósticos; só biblioteca padrão
      notation/       gramática de texto e de LaTeX, e a escrita da árvore de volta nas três formas
      catalog/        fichas homologadas e a versão do catálogo
      application/    validação guiada pela ficha, plano, orçamento e casos de uso
      algebra/        ponte entre a árvore e o SymPy, análise de domínio e teste de identidade
      numerics/       avaliação em dupla precisão, malha uniforme e Hamiltoniano tridiagonal
      solvers/        soluções fechadas, operações simbólicas, quadratura, DOP853, espectro e Crank-Nicolson
      verification/   verificadores independentes dos solvers, simbólicos e numéricos
      adapters/       unidades, constantes CODATA 2022, manifesto de ambiente e processo de cálculo
      interfaces/     leitura e escrita dos documentos JSON, esquemas e CLI
    reference_cases/  entradas, oráculos, derivações independentes e o corpus da notação
    docs/decisions/   decisões de plataforma, fronteiras, convenções físicas, arredondamento, notação e métodos numéricos
    docs/notation/    referência da gramática
    docs/evidence/    saída real do CLI que encerra cada fase

## Desenvolvimento

    uv run ruff format --check .
    uv run ruff check .
    uv run mypy
    uv run pytest

As identidades exatas e as comparações numéricas com tolerância rodam separadas: `uv run pytest -m algebraic` e `uv run pytest -m numerical`.

## Status

Funciona: o poço infinito, com unidades, constantes CODATA 2022 e propagação linear de incertezas independentes; a partir de um enunciado digitado, derivada ordinária ou parcial, primitiva, integral definida em intervalo sem singularidade, EDO linear escalar de primeira ordem com coeficientes constantes e revisão de candidata; e, por método numérico, integral definida, trajetória de sistema explícito não rígido, medição projetiva em base finita, espectro do poço infinito e do oscilador harmônico truncado e evolução temporal de uma superposição no poço.

Não existe ainda: API local, interface web, histórico e pacote de reprodução. São as fases 4 e 5 do roadmap. A ficha simbólica continua recusando a integral sem primitiva em forma fechada; a aproximação é pedida pela ficha numérica, com as tolerâncias escritas.

Limites conhecidos: os potenciais numéricos são só o nulo e o harmônico; a rigidez não é diagnosticada nem tratada; as fichas numéricas não propagam incerteza experimental; a evolução temporal mede o erro no tempo, não o da malha; as mensagens de uso geradas pelo `argparse` estão em inglês; o limite de memória do processo de cálculo é fixo em 2048 MiB; e a evidência registrada em `docs/evidence/` foi gerada fora da plataforma de referência, com a CI a reproduzindo em Ubuntu 24.04.

## Licença

GNU GPL versão 3. Veja `LICENSE`.
