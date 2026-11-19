# 0007 — Bancada local: API, fila, histórico e pacote de reprodução

Estado: aceita (fase 4). Estende as decisões 0002 e 0005.

## Contexto

A fase 4 põe uma interface na frente dos casos de uso do CLI. Um cálculo passa a durar mais que uma requisição, a ficar guardado, a ser comparado com outro e a ser entregue a outra pessoa. E a interface é uma página: qualquer outra página aberta no mesmo navegador também consegue enviar requisições ao servidor que roda na máquina do pesquisador.

## Decisão

Mesmos casos de uso. `qcalc serve` monta a bancada sobre uma pasta de dados e serve a API e a interface no mesmo endereço. A API e o CLI leem a entrada pelo mesmo `DocumentCalculator`: o corpo de `POST /validations` e de `POST /runs` é o documento que `qcalc validate` e `qcalc solve` recebem, e a resposta é o mesmo registro. A interface não calcula física, não converte unidade e não arredonda; trocar a unidade de exibição é uma leitura, `GET /runs/{id}/answers?unit=`, feita no servidor sobre o valor exato guardado.

API versionada. Tudo fica sob `/api/v1` e cada documento traz `api_version`. As rotas são `GET /catalog`, `POST /validations`, `POST /runs`, `GET /runs`, `GET /runs/{id}`, `POST /runs/{id}/cancellation`, `GET /runs/{id}/answers`, `GET /runs/{id}/tables/{nome}` e `.../csv`, `GET /runs/{id}/package`, `POST /imports` e `GET /comparisons`. Uma entrada recusada volta com 422 e o documento de recusa do CLI, com o ponteiro de cada diagnóstico.

Idempotência. `POST /runs` exige o cabeçalho `Idempotency-Key`, de 8 a 128 caracteres, e a chave é única na tabela de execuções. A mesma chave com a mesma entrada devolve a execução já criada, com 200 em vez de 202. A mesma chave com outra entrada é 409. A interface gera uma chave por tentativa e a reutiliza enquanto o texto da entrada não muda, então uma resposta perdida não duplica o cálculo.

Fila e processo. Uma execução roda por vez, no processo descartável da decisão 0005, com os mesmos limites de CPU, memória e tempo. Os estados são `queued`, `running`, `succeeded`, `failed`, `cancelled` e `interrupted`. Cada mudança de estado confere, dentro de uma transação de escrita, se a execução ainda está no estado esperado: cancelamento e conclusão concorrentes deixam um único estado final. Cancelar encerra o processo. Ao iniciar, a bancada marca como `interrupted` o que encontrou ativo e apaga os artefatos sem referência; ao encerrar, interrompe o que estiver rodando. Um resultado parcial nunca volta como verificado.

Histórico. SQLite em modo WAL, com tabelas `STRICT`, chaves estrangeiras ligadas e escrita em `BEGIN IMMEDIATE`. A entrada, o problema canônico e o desfecho ficam em arquivos nomeados pelo SHA-256 do conteúdo, publicados por inteiro antes da transação que os referencia. A versão do esquema de armazenamento fica em `PRAGMA user_version`; um histórico escrito por uma versão mais nova é recusado. Um registro não é alterado: mudar massa, largura, potencial ou método cria outra execução, ligada à anterior por `parent`. Registros com esquema de saída 1.0 e 1.1 continuam legíveis.

Comparação. `GET /comparisons` compara duas execuções em três partes: as diferenças da entrada, campo a campo; as versões da calculadora, da ficha, do esquema do registro, do catálogo, das constantes, do registro de unidades, do Python e das bibliotecas; e as respostas na mesma unidade, com a razão entre elas. A divergência de versão aparece antes das respostas.

Pacote de reprodução. Um ZIP com `manifest.json`, `input.json`, `problem.json`, `outcome.json`, `answers.csv` e uma tabela CSV por série em `tables/`. O manifesto declara o esquema `reproduction_package` 1.0, o gerador, a execução e o tamanho e o SHA-256 de cada arquivo; a entrada vai byte a byte como foi enviada; os CSV trazem a unidade no cabeçalho. Nenhum arquivo leva caminho da máquina de origem. A importação aceita até 64 MiB, 64 arquivos e 32 MiB por arquivo, recusa caminho absoluto ou com `..`, atalho e arquivo cifrado, e confere cada hash, o hash do problema canônico e a coerência entre manifesto e registro antes de guardar qualquer coisa. Importar não calcula: a execução entra marcada como importada, e reexecutar é um pedido à parte, que cria outra execução ligada a ela.

Acesso. O servidor escuta só em `127.0.0.1` e confere `Host` e `Origin` em toda requisição, com 421 e 403. O segredo de sessão nasce com o processo e morre com ele. `qcalc serve` escreve na pasta de dados, com permissão 0600, o arquivo `abrir-calculadora.html`, que envia o código de acesso por POST e recebe um cookie `HttpOnly`, `SameSite=Strict`, restrito a `/api/v1`. O segredo não passa por URL nem fica ao alcance de script. As respostas levam uma CSP sem origem de terceiros, `frame-ancestors 'none'` e, na API, `Cache-Control: no-store`.

Interface. React 19 e TypeScript em `web/`, compilados pelo Vite para `src/quantum_calculator/interfaces/api/static/`. Esse diretório não é versionado: entra no wheel como artefato de build, e quem instala o wheel não precisa de Node.js. As fontes e o KaTeX vão empacotados, então a página não pede nada fora da máquina. As rotas ficam no fragmento da URL. As respostas da API são validadas com Valibot antes de chegar a um componente. Os gráficos são SVG próprio, com eixos, unidades, traços distinguíveis sem cor e a mesma série em tabela e em CSV. Amplitude e densidade nunca dividem um eixo: cada unidade tem o seu.

Registro operacional. Uma linha por execução, com identificador, ficha, estado final, duração e categoria de falha. Enunciado, parâmetros e resultado não vão para o log.

## O que ficou de fora

Execuções em paralelo: a fila é serial. Contas e uso por mais de uma pessoa. Exclusão de execução e limpeza do histórico pela interface. Paginação do histórico. Animação da evolução temporal: a série sai amostrada nos instantes salvos.

## Quando rever

Se dois cálculos longos precisarem rodar juntos, com orçamento de memória por execução. Se o histórico crescer a ponto de a lista inteira pesar na tela. Se outra plataforma for homologada, porque a permissão do arquivo de acesso e da pasta de dados é POSIX.
