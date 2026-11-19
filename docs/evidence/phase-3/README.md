# Evidência de encerramento da fase 3

Saída real do CLI para os problemas numéricos, gerada de uma instalação limpa: wheel construído do repositório e instalado em um ambiente virtual novo, só com as dependências de execução do `uv.lock`.

| Evidência pedida pelo roadmap | Onde está |
| --- | --- |
| Entradas de referência | `reference_cases/numerical/`: uma por ficha, mais as variações de base e fase global, de degenerescência, de malha grossa e de domínio estreito |
| Oráculos independentes e tolerâncias | `reference_cases/numerical/expectations.json`, com a conta de cada valor esperado |
| Saídas de referência e dados brutos | `<caso>.solve.txt` para os dez casos e `<caso>.run_record.json` para sete deles, com respostas, tabelas completas, parâmetros efetivos e verificação |
| Tabelas de erro por nível e malha | seção "Erro por nível e malha", tirada das tabelas `refinement` e `truncation` dos registros |
| Relatórios de norma e fase | seção "Norma e fase", tirada de `electron_box_1nm_beat.run_record.json` |
| Casos de falha | seção "Casos de falha": os arquivos `*.rejection.txt` e os dois relatórios com verificação não aprovada |
| Versões efetivas das bibliotecas numéricas | campo `environment` de cada registro e seção "Bibliotecas" |
| Relatório da suíte | `suite_report.txt`; na CI, o artefato `test-reports` traz o JUnit de cada etapa |

Também ficam aqui duas prévias sem cálculo, `electron_box_1nm_discrete.validate.txt` e `sine_quadrature.validate.txt`.

## Erro por nível e malha

Poço infinito de 1 nm, `electron_box_1nm_discrete.run_record.json`. A energia analítica é n² vezes 0,3760301621 eV, o valor da fase 1; ela não vem do solver discreto. A ordem é o logaritmo na base 2 da razão entre os erros de duas malhas seguidas.

| Nível | Subintervalos | Energia discreta (eV) | Energia analítica (eV) | Erro relativo | Ordem observada |
| --- | --- | --- | --- | --- | --- |
| 1 | 128 | 0.3760112860 | 0.3760301621 | 5.020e-05 |  |
| 1 | 256 | 0.3760254430 | 0.3760301621 | 1.255e-05 | 2.000 |
| 1 | 512 | 0.3760289823 | 0.3760301621 | 3.137e-06 | 2.000 |
| 2 | 128 | 1.5038186488 | 1.5041206484 | 2.008e-04 |  |
| 2 | 256 | 1.5040451440 | 1.5041206484 | 5.020e-05 | 2.000 |
| 2 | 512 | 1.5041017720 | 1.5041206484 | 1.255e-05 | 2.000 |
| 3 | 128 | 3.3827427395 | 3.3842714589 | 4.517e-04 |  |
| 3 | 256 | 3.3838892273 | 3.3842714589 | 1.129e-04 | 2.000 |
| 3 | 512 | 3.3841758978 | 3.3842714589 | 2.824e-05 | 2.000 |

Com 512 subintervalos, que são 511 incógnitas internas, a resposta sai com o erro de malha estimado por Richardson: E_1 = 0.3760289823 eV com 0.0000012 eV, E_2 = 1.504101772 eV com 0.000019 eV e E_3 = 3.384175898 eV com 0.000096 eV. O resíduo do operador discreto é outra medida, relatada à parte: maior resíduo adimensional: 1.642e-16, dentro do limite 1.000e-10; ortonormalidade ponderada, maior desvio da identidade: 2.220e-16, dentro do limite 1.000e-10.

O mesmo poço com 16 subintervalos, `electron_box_1nm_coarse.run_record.json`. O resíduo discreto continua na casa de 1e-16, mas o estudo de malha fica `inconclusive` e o processo termina com código 5:

| Nível | Subintervalos | Energia discreta (eV) | Energia analítica (eV) | Erro relativo | Ordem observada |
| --- | --- | --- | --- | --- | --- |
| 1 | 4 | 0.3570937357 | 0.3760301621 | 5.036e-02 |  |
| 1 | 8 | 0.3712225528 | 0.3760301621 | 1.279e-02 | 1.978 |
| 1 | 16 | 0.3748236182 | 0.3760301621 | 3.209e-03 | 1.994 |
| 2 | 4 | 1.2191942755 | 1.5041206484 | 1.894e-01 |  |
| 2 | 8 | 1.4283749429 | 1.5041206484 | 5.036e-02 | 1.911 |
| 2 | 16 | 1.4848902114 | 1.5041206484 | 1.279e-02 | 1.978 |
| 3 | 4 | 2.0812948153 | 3.3842714589 | 3.850e-01 |  |
| 3 | 8 | 3.0105153018 | 3.3842714589 | 1.104e-01 | 1.802 |
| 3 | 16 | 3.2875405429 | 3.3842714589 | 2.858e-02 | 1.950 |

O verificador mede a ordem pelas diferenças entre malhas, sem a expressão fechada: ordem observada entre 1.746 e 1.972 com 4, 8 e 16 subintervalos: a malha não está no regime assintótico e não é declarada convergida.

Oscilador harmônico de 1 eV entre menos e mais oito comprimentos do oscilador, `harmonic_oscillator_1ev.run_record.json`, contra hbar omega (n + 1/2):

| Nível | Subintervalos | Energia discreta (eV) | Energia analítica (eV) | Erro relativo | Ordem observada |
| --- | --- | --- | --- | --- | --- |
| 1 | 256 | 0.4998778999 | 0.5000000000 | 2.442e-04 |  |
| 1 | 512 | 0.4999694806 | 0.5000000000 | 6.104e-05 | 2.000 |
| 1 | 1024 | 0.4999923705 | 0.5000000000 | 1.526e-05 | 2.000 |
| 2 | 256 | 1.4993893799 | 1.5000000000 | 4.071e-04 |  |
| 2 | 512 | 1.4998473953 | 1.5000000000 | 1.017e-04 | 2.000 |
| 2 | 1024 | 1.4999618520 | 1.5000000000 | 2.543e-05 | 2.000 |
| 3 | 256 | 2.4984120410 | 2.5000000000 | 6.352e-04 |  |
| 3 | 512 | 2.4996032063 | 2.5000000000 | 1.587e-04 | 2.001 |
| 3 | 1024 | 2.4999008138 | 2.5000000000 | 3.967e-05 | 2.000 |

O corte do domínio é outro experimento. O solver repete o cálculo de 8 para 10 comprimentos do oscilador com o mesmo espaçamento, e a mudança fica nove ordens abaixo do erro de malha:

| Nível | Energia com meia largura 2.20834e-09 (eV) | Energia com meia largura 2.76043e-09 (eV) | Mudança relativa pelo corte | Erro de malha relativo estimado |
| --- | --- | --- | --- | --- |
| 1 | 0.499992370490 | 0.499992370489 | 1.115e-12 | 1.526e-05 |
| 2 | 1.499961851980 | 1.499961851980 | 2.167e-13 | 2.544e-05 |
| 3 | 2.499900813796 | 2.499900813796 | 2.816e-13 | 3.968e-05 |

Com meia largura 3, `harmonic_oscillator_narrow.solve.txt`, a situação se inverte: `mesh_refinement` passa, `domain_truncation` falha e o resultado termina com código 5. A malha fina não esconde o domínio pequeno.

## Norma e fase

Superposição igual dos dois primeiros estados do poço, por um período de batimento do poço contínuo, 8 m L² / (3 h) = 3,666077985 fs, em 1024 passos e 256 subintervalos. A referência da fase é a evolução exata dos dois modos discretos, o que isola o erro temporal.

| Instante (s) | Norma menos 1 | Fase relativa (rad) | Fase exata dos modos discretos (rad) | Erro de fase (rad) |
| --- | --- | --- | --- | --- |
| 0.000000e+00 | +0.000e+00 | +0.000000000 | +0.000000000 | 0.000e+00 |
| 4.582597e-16 | -2.776e-15 | -0.785343133 | -0.785348881 | 5.749e-06 |
| 9.165195e-16 | -4.885e-15 | -1.570686265 | -1.570697763 | 1.150e-05 |
| 1.374779e-15 | -6.550e-15 | -2.356029398 | -2.356046644 | 1.725e-05 |
| 1.833039e-15 | -7.550e-15 | -3.141372530 | -3.141395525 | 2.300e-05 |
| 2.291299e-15 | -9.326e-15 | +2.356469645 | +2.356440901 | 2.874e-05 |
| 2.749558e-15 | -1.066e-14 | +1.571126512 | +1.571092019 | 3.449e-05 |
| 3.207818e-15 | -1.321e-14 | +0.785783379 | +0.785743138 | 4.024e-05 |
| 3.666078e-15 | -1.554e-14 | +0.000440247 | +0.000394257 | 4.599e-05 |

Deriva máxima da norma nos instantes salvos: 1.554e-14, sem renormalização entre passos. Erro máximo da fase relativa: 4.599e-05 rad. O verificador relata: deriva máxima da norma: 1.554e-14, dentro do limite 1.000e-09; ordem observada 2.000 entre 512 e 1024 passos; maior diferença para a fase prevista pelo esquema, em rad: 5.811e-12, dentro do limite 1.000e-08.

| Passos | Erro da fase relativa no instante final (rad) | Ordem observada |
| --- | --- | --- |
| 256 | 7.357296e-04 |  |
| 512 | 1.839549e-04 | 2.000 |
| 1024 | 4.599013e-05 | 2.000 |

## Casos de falha

| Arquivo | Entrada | Código de saída | Diagnóstico |
| --- | --- | --- | --- |
| `divergent_integral.rejection.txt` | `rejected/divergent_integral.json` | 9 | `non_convergent`, `method_not_converged`: a quadratura não atinge a tolerância em 1/x através de zero |
| `blow_up_trajectory.rejection.txt` | `rejected/blow_up_trajectory.json` | 9 | `non_convergent`, `method_not_converged`: o passo do DOP853 colapsa antes do fim do intervalo |
| `resource_limit.rejection.txt` | `rejected/resource_limit.json` | 7 | `resource_limit_exceeded` em `/numerics/subintervals`, antes de alocar |
| `estimated_work_too_large.rejection.txt` | `rejected/estimated_work_too_large.json` | 7 | `resource_limit_exceeded` em `/numerics`: a estimativa de trabalho passa do perfil |
| `time_budget_exceeded.rejection.txt` | `electron_box_1nm_discrete.json` com `--time-limit 0.05` | 7 | `time_budget_exceeded`: o processo de cálculo é encerrado |
| `non_hermitian_operator.rejection.txt` e `.json` | `rejected/non_hermitian_operator.json` | 3 | `non_hermitian_operator` em `/observable/matrix` |
| `zero_state.rejection.txt` | `rejected/zero_state.json` | 3 | `zero_state` em `/state` |
| `incompatible_condition.rejection.txt` | `rejected/incompatible_condition.json` | 3 | `incompatible_condition` em `/conditions/1` |
| `missing_initial_state.rejection.txt` | `rejected/missing_initial_state.json` | 3 | `missing_field` em `/initial_state` |
| `electron_box_1nm_coarse.solve.txt` | `electron_box_1nm_coarse.json` | 5 | resultado calculado, verificação `inconclusive` em `mesh_refinement` |
| `harmonic_oscillator_narrow.solve.txt` | `harmonic_oscillator_narrow.json` | 5 | resultado calculado, verificação `failed` em `domain_truncation` |

Nas recusas o arquivo guarda a saída de erro; a saída padrão fica vazia.

## Bibliotecas

CPython 3.12.15; Linux-6.18.56-x86_64-with-glibc2.34; sympy 1.14.0; mpmath 1.3.0; numpy 2.5.5; scipy 1.18.1.

| Biblioteca | Interface | Implementação ligada | Versão |
| --- | --- | --- | --- |
| numpy | blas | scipy-openblas | 0.3.34.237.2 |
| numpy | lapack | scipy-openblas | 0.3.34.237.2 |
| scipy | blas | scipy-openblas | 0.3.31.dev |
| scipy | lapack | scipy-openblas | 0.3.31.dev |

## Como foi gerada

    uv build --wheel --out-dir dist
    uv export --locked --no-dev --no-emit-project --output-file runtime-requirements.txt
    uv venv --python 3.12 clean-environment
    uv pip install --python clean-environment/bin/python --require-hashes --requirement runtime-requirements.txt
    uv pip install --python clean-environment/bin/python --no-deps dist/*.whl
    clean-environment/bin/qcalc validate reference_cases/numerical/electron_box_1nm_discrete.json
    clean-environment/bin/qcalc validate reference_cases/numerical/sine_quadrature.json
    clean-environment/bin/qcalc solve reference_cases/numerical/CASO.json
    clean-environment/bin/qcalc solve reference_cases/numerical/CASO.json --format json
    clean-environment/bin/qcalc solve reference_cases/numerical/rejected/CASO.json
    clean-environment/bin/qcalc solve reference_cases/numerical/rejected/non_hermitian_operator.json --format json
    clean-environment/bin/qcalc solve reference_cases/numerical/electron_box_1nm_discrete.json --time-limit 0.05

`CASO` percorre os dez casos aceitos no relatório em texto, os sete com registro JSON e as oito recusas da tabela acima.

## Limite desta evidência

Os arquivos foram gerados em Amazon Linux 2023 (kernel 6.18, glibc 2.34) com CPython 3.12.15, como o manifesto registra, e não na plataforma de referência.

Um resultado em dupla precisão não é comparado bit a bit entre máquinas. `tests/contracts/test_recorded_numerical_evidence.py` compara cada registro JSON com a saída atual: o conteúdo declarado tem de ser igual, e cada resposta, estimativa e valor de tabela tem de concordar dentro de 1e-6 do próprio valor ou de 1e-9 da maior magnitude que o registro guarda na mesma unidade, o que for maior. A tolerância absoluta tem assim a unidade e a escala da grandeza: um nó de autofunção, um valor esperado nulo ou um desvio de norma não são comparados em termos relativos, e uma posição em metros não é comparada com um limite adimensional. As prévias e as recusas são texto determinístico e são comparadas byte a byte. Os relatórios `*.solve.txt` são o retrato desta execução: algarismos no nível do arredondamento, como a deriva da norma, mudam com a biblioteca de álgebra linear, então o teste confere só a estrutura e o veredito deles.

A CI repete a geração em Ubuntu 24.04 e compara a prévia do poço, a recusa da integral divergente e, em cada registro, o veredito, o estado de cada checagem e as respostas arredondadas em 1e-6. `suite_report.txt` é o retrato da execução que fechou a fase.

A saída mudou de formato nesta fase: o esquema de saída passou a 1.2, com os documentos `numerical_validation` e `numerical_run_record`, e o catálogo passou a 1.2.0. Por isso a evidência das fases 1 e 2 foi regenerada pelo mesmo procedimento.

## Critérios de aceite

- Todas as famílias publicadas passam em seus casos. `tests/integration/test_cli_numerical.py` compara cada resposta com o oráculo de `expectations.json` na tolerância do roadmap, confere a trajetória nos 51 instantes, a ordem de convergência do poço contra as energias analíticas e a concordância entre o caminho analítico e o discreto dentro de duas vezes o erro de malha estimado. `tests/contracts/test_catalog_examples.py` resolve e verifica o exemplo de cada ficha.
- O relatório separa resíduo, discretização e corte de domínio nas checagens `discrete_residual`, `mesh_refinement` e `domain_truncation`. O caso sub-resolvido sai `inconclusive`, nunca como malha convergida, e o domínio estreito falha só no corte.
- A evolução confere norma e fase com `norm_conservation`, `relative_phase`, `scheme_dispersion` e `temporal_order`. Nenhum teste exige igualdade bit a bit entre bibliotecas numéricas.
- Falha de convergência, domínio inválido e cancelamento não deixam resposta nem processo: `tests/integration/test_cli_numerical_refusals.py`, `tests/unit/application/test_solve_numerical.py` e, com um SIGINT de verdade, `tests/e2e/test_module_entry_point.py` conferem a saída vazia, o código de saída e a ausência de processos filhos.

Ficou de fora, e as fichas dizem isso: rigidez, potenciais além do nulo e do harmônico, incerteza experimental nas fichas numéricas e erro de malha na evolução temporal, que mede só o erro no tempo.
