# Evidência de encerramento da fase 4

Saída real da bancada, percorrida de ponta a ponta a partir de uma instalação limpa: a interface compilada entra no wheel, o wheel é instalado em um ambiente virtual novo só com as dependências de execução do `uv.lock`, e os percursos rodam em um namespace de rede em que só a interface de loopback existe.

| Evidência pedida pelo roadmap | Onde está |
| --- | --- |
| Testes ponta a ponta | `suite_report.txt`: os 21 percursos de `web/e2e/`, cada um com o próprio `qcalc serve` em uma pasta de dados vazia |
| Pacote exportado e reimportado | `electron_box_1nm.package.zip`, o manifesto dele em `electron_box_1nm.package.manifest.json` e `electron_box_1nm.altered_package.zip`, com um algarismo trocado depois da exportação |
| Relatório de acessibilidade | `accessibility_report.json` e a seção "Acessibilidade" |
| Registro de uma sessão de revisão com usuário do público-alvo | não existe; veja "Sessão de revisão com o público-alvo" |
| Relatório da suíte | `suite_report.txt`; na CI, os artefatos `test-reports` e `phase-4-workbench` |

## Percursos

Cada teste obrigatório do roadmap tem um percurso em `web/e2e/`. As frases entre aspas são o texto que a tela mostra.

| Teste obrigatório | Percurso | O que acontece |
| --- | --- | --- |
| Resolver o poço e trocar 1 nm por 2 nm | `well-energy.spec.ts` | `E = 0.3760301621 eV` e depois `E = 0.09400754053 eV`, em duas execuções. A comparação lista `grandezas › largura do poço (L) › valor`, de 1 para 2, e a razão 0.25 entre as respostas. Mostrar o valor em meV ou em J não envia cálculo: o percurso inteiro faz dois envios |
| Rever uma candidata de EDO incorreta | `candidate-review.spec.ts` | Para `y(t) = 2*y_0*exp(-k*t)` com `y(0) = y_0`, a resposta abre com "A verificação reprovou este resultado", "Checagem reprovada: A função informada assume o valor declarado no ponto da condição inicial." e "Observado: o resíduo y_0 não se anula". A entrada original em JSON fica fechada. A candidata corrigida é aprovada e as duas ficam no histórico |
| Encerrar um worker, reiniciar, cancelar e repetir a submissão | `calculation-lifecycle.spec.ts` | SIGKILL no processo de cálculo: "O cálculo terminou sem resultado", e a bancada calcula o poço em seguida. SIGKILL na bancada no meio de um cálculo, e reinício: a execução volta como "interrompida", sem valor e sem verificação, e a anterior continua aprovada. Cancelar: o processo de cálculo some e o cálculo seguinte roda. Resposta do envio perdida e envio repetido: uma execução só no histórico |
| Importar pacote válido e pacote com artefato alterado, sem enviar nada para fora | `reproduction-package.spec.ts` | Seção "Pacote exportado e reimportado" |
| Teclado, leitor de tela e janela estreita | `keyboard-journey.spec.ts`, `accessibility.spec.ts` | Seção "Acessibilidade" |

Os outros percursos cobrem o resto das entregas. Em `calculation-lifecycle.spec.ts`, massa negativa e nível zero são apontados cada um no próprio campo, a malha de 16 subintervalos sai como "inconclusiva" e a solução geral de `y' = a*y + s` sai como "condicional", com o caso `a = 0` escrito. Em `tables-and-series.spec.ts`, o espectro é uma tabela, as autofunções são séries com eixos e unidades e a densidade tem eixo e unidade próprios. Em `session.spec.ts`, uma página que não veio do arquivo de acesso recebe 401 em `/api/v1/catalog` e em `/api/v1/runs`.

Nada sai da máquina por dois caminhos. `web/e2e/support/fixtures.ts` reprova qualquer percurso em que a página peça um endereço que não seja `http://127.0.0.1`. E os 21 percursos passaram dentro de `unshare --net`, com só a interface `lo` ativa, depois de uma tentativa de alcançar `https://github.com` falhar ali dentro.

## Pacote exportado e reimportado

`electron_box_1nm.package.zip` é o arquivo que a bancada entregou no percurso "reproduces on an empty profile the package exported by another bench", para o poço de 1 nm preenchido no formulário.

| Arquivo | Bytes | Conteúdo |
| --- | --- | --- |
| `manifest.json` | 1411 | esquema `reproduction_package` 1.0, gerador `quantum-calculator` 0.4.0, a execução e o tamanho e o SHA-256 de cada arquivo |
| `input.json` | 423 | a entrada, byte a byte como foi enviada |
| `problem.json` | 1750 | o problema canônico; o SHA-256 dele é o `canonical_problem_sha256` do manifesto |
| `outcome.json` | 7754 | o registro com resultado, verificação e ambiente |
| `answers.csv` | 120 | a resposta, com a unidade em coluna própria |

    grandeza,símbolo,descrição,valor,unidade,erro estimado,origem do erro
    energy,E,energia do nível,0.3760301621,eV,,

No mesmo percurso, uma segunda bancada, com a pasta de dados vazia, importa o arquivo. A execução aparece como "importada" e "concluída", com `E = 0.3760301621 eV` e o aviso "Nada foi recalculado nesta instalação."; nenhum processo de cálculo é criado. "Reexecutar nesta instalação" cria outra execução, e a comparação diz que as duas registram as mesmas versões, que as entradas são iguais e que a razão entre as respostas é 1. Nenhum arquivo do pacote contém a pasta de dados da bancada que o escreveu nem o diretório do usuário.

`electron_box_1nm.altered_package.zip` vem do percurso "refuses a package with an altered artifact before calculating anything". É o pacote que outra bancada exportou para a mesma entrada, com `0.3760301621` trocado por `0.3760301622` em `answers.csv` e o manifesto como estava. A importação responde 422 com `package_refused` e "o arquivo answers.csv não confere com o hash declarado no manifesto". A tela diz "Nada foi importado nem calculado.", o histórico continua vazio e nenhum processo de cálculo é criado.

Em "shows the version divergence of an imported package before the answers", um pacote cujo manifesto declara a calculadora 0.1.0 é importado e reexecutado. A comparação abre com "As execuções usaram versões diferentes", mostra 0.1.0 na linha `calculadora`, e a região "Versões" fica acima de "Respostas".

`tests/contracts/test_recorded_workbench_evidence.py` repete isso com os dois arquivos desta pasta a cada execução da suíte: importa o pacote sem calcular, reexecuta e obtém razão `1` com o mesmo hash do problema canônico, vê o pacote alterado ser recusado sem nada guardado e compara `electron_box_1nm.package.manifest.json` byte a byte com o manifesto de dentro do ZIP.

## Acessibilidade

`accessibility_report.json` tem 18 auditorias: nove telas, cada uma em 1280 x 720 e em 320 x 640, com o axe-core 4.14.1 e as regras marcadas `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` e `wcag22aa`. Não há violação, e nenhuma tela rola para o lado: `horizontal_overflow_px` é 0 nas 18.

| Tela | Regras aprovadas, janela larga | Regras aprovadas, janela estreita | Violações | Elementos sem decisão, larga | Elementos sem decisão, estreita |
| --- | --- | --- | --- | --- | --- |
| sessão não aberta | 19 | 19 | 0 | 0 | 0 |
| catálogo de problemas | 20 | 20 | 0 | 0 | 0 |
| formulário da ficha | 28 | 28 | 0 | 0 | 0 |
| entrada recusada | 30 | 30 | 0 | 0 | 0 |
| interpretação conferida | 32 | 33 | 0 | 0 | 2 |
| resultado com uma grandeza | 30 | 31 | 0 | 5 | 6 |
| comparação de execuções | 25 | 26 | 0 | 0 | 3 |
| resultado com tabelas e séries | 31 | 32 | 0 | 13 | 24 |
| histórico | 26 | 27 | 0 | 0 | 20 |

Os 73 elementos sem decisão são todos da regra `color-contrast`. O axe não os aprova nem reprova, e diz por quê: texto curto demais para ser tratado como texto, fundo parcialmente coberto por outro elemento ou elemento com imagem dentro. O que se pode dizer deles vem dos tokens de `web/src/styles/theme.css`, a única fonte de cor do texto da interface. O par mais fraco em uso é `muted` sobre `paper`, com 5,87:1; `signal` dá 6,67:1, `primary` 7,79:1 e `ink` 14,88:1 sobre o mesmo fundo, e o texto branco sobre `primary` dá 8,53:1. O critério AA pede 4,5:1 para texto de tamanho normal. Essas razões foram calculadas dos tokens pela fórmula de luminância relativa da WCAG, não medidas elemento a elemento na tela.

`keyboard-journey.spec.ts` vai da pergunta ao pacote exportado com Tab, Shift+Tab, Enter, Espaço, as setas nas listas de unidade e digitação. Começa pelo atalho "Ir para o conteúdo", escolhe a ficha, marca as hipóteses e digita uma massa negativa. Ao pedir a interpretação, o foco vai para a região da conferência, que lista um problema em `grandezas › massa da partícula (m) › valor`; o campo fica com `aria-invalid` e com a descrição "deve ser estritamente positivo". O percurso volta ao campo com Shift+Tab, corrige, confirma, calcula, mostra o valor em meV e exporta o pacote com Enter. A cada troca de tela o foco está na região principal.

O percurso "gives assistive technology the quantity, the unit and the state of a result in words" compara a árvore de acessibilidade da resposta: o título "Resposta", "energia do nível", "E = 0.3760301621 eV", a expressão como matemática com a alternativa "(em texto: E_n = h**2*n**2/(8*L**2*m))" e a lista "Unidade de exibição" descrita por "A conversão usa o valor guardado. O cálculo não é refeito.". O estado sai em palavras, "concluída" e "verificação aprovada". Em 320 px o valor cabe inteiro na janela.

## Sessão de revisão com o público-alvo

Não foi feita. O roadmap pede o registro de uma sessão com uma pessoa do público-alvo, um pesquisador que não programa, e nenhum teste desta pasta ocupa esse lugar: os percursos mostram que a tela faz o que foi especificado, não que um físico a entende. Enquanto esse registro não existir, a fase 4 não está encerrada pelo critério do roadmap.

A sessão cabe nos testes obrigatórios, feitos pela pessoa sem ajuda e sem abrir código, log ou JSON:

1. Resolver o poço de 1 nm, alargar para 2 nm e dizer por que a energia mudou e para quanto.
2. Rever a candidata `y(t) = 2*y_0*exp(-k*t)` para `y' = -k*y` com `y(0) = y_0` e dizer o que está errado nela.
3. Carregar `tests/fixtures/inputs/long_time_evolution.json` na ficha de evolução temporal, cancelar o cálculo e dizer o que ficou dele no histórico.
4. Exportar um pacote, importá-lo em uma bancada aberta com outro `--data-dir` e reexecutá-lo.
5. Repetir o primeiro item só com o teclado e, se a pessoa usar um, com o leitor de tela dela.

O registro entra nesta pasta como `review_session.md`, com a data, a versão da calculadora, a formação da pessoa, o que ela fez sozinha em cada item, onde parou ou leu errado e o que mudou na interface por causa disso.

## Como foi gerada

    cd web && npm ci && npm run build && cd ..
    uv build --wheel --out-dir dist
    uv export --locked --no-dev --no-emit-project --output-file runtime-requirements.txt
    uv venv --python 3.12 clean-environment
    uv pip install --python clean-environment/bin/python --require-hashes --requirement runtime-requirements.txt
    uv pip install --python clean-environment/bin/python --no-deps dist/*.whl
    cd web
    sudo unshare --net -- sh -c '
      ip link set lo up
      if curl --silent --max-time 5 --output /dev/null https://github.com; then exit 1; fi
      exec sudo --set-home --user "$1" env "PATH=$2" "QCALC_COMMAND=$3" "QCALC_ACCESSIBILITY_REPORT=$4" CI=true npx playwright test --reporter=list
    ' unplugged "$(id -un)" "$PATH" "$PWD/../clean-environment/bin/qcalc" "$PWD/accessibility_report.json"

O wheel saiu com 75 arquivos em `quantum_calculator/interfaces/api/static/`. Os dois pacotes foram copiados de `web/test-results/`, de `exported.zip` e `altered.zip` nas pastas dos dois percursos, e o manifesto foi tirado do primeiro com `unzip -p`. `suite_report.txt` junta a última linha de cada check e a lista dos percursos.

## Limite desta evidência

Os arquivos foram gerados em Amazon Linux 2023 (kernel 6.18, glibc 2.34) com CPython 3.12.15 e Node.js 24.16.0, e não na plataforma de referência. O job `workbench` da CI repete a compilação da interface, o wheel, a instalação limpa e os percursos sem rede em Ubuntu 24.04, e publica em `phase-4-workbench` o relatório do Playwright, o relatório de acessibilidade e os pacotes exportados.

O navegador é um só, o Chrome Headless Shell 159.0.8154.6. Firefox e Safari não foram exercitados.

O axe cobre a parte da WCAG 2.2 que uma regra automática alcança. Zero violações não é uma declaração de conformidade, e os 73 elementos de contraste ficaram sem medição na tela.

Ninguém ouviu a interface em um leitor de tela. O percurso confere a árvore que o NVDA, o Orca ou o VoiceOver recebem, não o que uma pessoa escuta com eles.

O identificador da execução e os instantes gravados no manifesto são desta geração. O teste de contrato não os compara: confere o estado, a verificação, a resposta e os hashes.

## Critérios de aceite

- CLI e interface produzem o mesmo problema canônico, o mesmo método e o mesmo resultado. Em "records through the interface what the command line prints for the same input", o `problem.json` do pacote é o que `qcalc validate --format json` imprime para o `input.json` do mesmo pacote, e o `outcome.json` é o que `qcalc solve --format json` imprime, fora o ambiente. `tests/integration/test_cli_and_api_agree.py` faz a mesma comparação pela API para cinco casos de referência, das fichas fechada, simbólica e numérica.
- O cenário do poço é feito sem programar, só com o formulário, em `well-energy.spec.ts` e, pelo teclado, em `keyboard-journey.spec.ts`. A ficha do resultado traz a resposta, o problema e as hipóteses, o método, a precisão, as verificações e os dados de reprodução.
- Uma instalação limpa importa e reexecuta o pacote, que não leva caminho da máquina de origem: `reproduction-package.spec.ts`, `tests/integration/test_api_packages.py` e o teste de contrato sobre os arquivos desta pasta. A divergência de versão aparece antes das respostas.
- O histórico sobrevive ao reinício, uma falha não toca nos resultados anteriores e cancelar libera o processo: `tests/unit/adapters/test_sqlite_runs.py`, `tests/unit/workbench/test_recover_history.py`, `tests/unit/workbench/test_execute_run.py`, que inclui o cancelamento que corre junto com a conclusão, `tests/integration/test_workbench_session.py` e, com a bancada morta por SIGKILL, `tests/e2e/test_serve_command.py`.

Ficou de fora, e a decisão 0007 diz isso: execuções em paralelo, exclusão de execução pela interface, paginação do histórico e animação da evolução temporal.
