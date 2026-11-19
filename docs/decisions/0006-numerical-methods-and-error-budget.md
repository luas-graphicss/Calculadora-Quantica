# 0006 — Métodos numéricos, orçamento de erro e perfil de recursos

Estado: aceita (fase 3). Estende as decisões 0002 e 0005.

## Contexto

A fase 3 passa a devolver respostas aproximadas. Um número em dupla precisão sem erro caracterizado parece tão exato quanto o analítico; um resíduo pequeno do problema discreto se confunde com convergência ao problema contínuo; e um pedido grande pode alocar memória antes de alguém saber o tamanho dele.

## Decisão

Entrada própria. O problema numérico é um terceiro documento de entrada, com esquema `numerical`. Ele traz a ficha, as hipóteses e os parâmetros como na fase 1, ou o enunciado como na fase 2, e o bloco `numerics` com malha, passos e tolerâncias. `numerics` é obrigatório e cada ajuste é lido pelo nome: um ajuste ausente ou desconhecido recusa a entrada. Nada é escolhido em silêncio, nem a normalização de um estado.

Escalas. Os parâmetros são convertidos uma vez para o SI. Os problemas de Schrödinger são resolvidos em unidades reduzidas de comprimento, energia e tempo, registradas nos parâmetros efetivos do resultado; as unidades voltam na saída. A tolerância absoluta vale na unidade coerente do SI do resultado e é combinada com a relativa, para que a comparação perto de zero não dependa só de uma razão.

Métodos. Quadratura adaptativa do QUADPACK e `solve_ivp` com DOP853, sem tratamento de rigidez. Base finita com `numpy.linalg.eigh`, depois de conferidas a forma, a norma, a base e a hermiticidade. Hamiltoniano em uma dimensão por diferenças centrais de segunda ordem nos nós internos, guardado como duas diagonais; os níveis saem de `scipy.linalg.eigh_tridiagonal`, selecionados por índice, sem matriz densa. As autofunções são normalizadas pela integral na malha, com os extremos restaurados. A evolução usa Crank-Nicolson: o sistema tridiagonal complexo é fatorado uma vez pelo LAPACK e reutilizado em todos os passos, sem inversa explícita e sem renormalizar o estado.

Três erros, três checagens. O resíduo do operador discreto (`discrete_residual`) confere a álgebra. A discretização (`mesh_refinement`) é medida repetindo o cálculo com um quarto e com a metade da malha: fora da ordem observada entre 1,8 e 2,2 a malha não é declarada convergida e a verificação fica `inconclusive`. O corte do domínio (`domain_truncation`) é medido ampliando o domínio com o mesmo espaçamento. O erro de malha estimado por Richardson acompanha cada energia, com a origem escrita; não é intervalo de confiança experimental.

Verificador independente. Nenhum verificador usa a saída interna do solver como valor esperado. A quadratura é refeita por Gauss-Legendre composto. A trajetória é refeita com tolerâncias mais apertadas. A medição é conferida por projetores de subespaço construídos do observável, sem os autovetores do solver, e por invariância de fase global. O espectro é conferido pelo resíduo, pela contagem de autovalores abaixo de cada nível e, quando o modelo tem expressão fechada, por ela. A evolução é comparada com a evolução exata dos modos discretos e com a dispersão prevista para o esquema, o que isola o erro temporal.

Perfil de recursos. Antes de alocar, a validação estima memória e operações a partir de níveis, nós, passos e amostras. Acima do perfil homologado, de 256 MiB e 2e9 operações estimadas, a entrada é recusada com `resource_limit_exceeded`. A evolução guarda só os observáveis dos instantes pedidos e a densidade final. O cálculo roda no processo descartável da decisão 0005, com os mesmos limites e o mesmo cancelamento.

Falhas. `method_not_converged` e `non_finite_result` formam a categoria `non_convergent`, com código de saída 9. A última iteração de um método que não terminou nunca vira resposta.

Saída. O registro numérico traz as respostas como números em dupla precisão, com a exibição arredondada à parte, as tabelas completas, os parâmetros efetivos e a verificação. O esquema de saída passou a 1.2 com os documentos `numerical_validation` e `numerical_run_record`, e o catálogo a 1.2.0.

| Pacote | Responsabilidade | Pode importar |
| --- | --- | --- |
| `domain/numerical` | Fichas, entrada, problemas tipados, relatório e álgebra complexa pequena | `domain` |
| `application/numerical` | Leitura dos ajustes, validação por família, escalas e estimativa de recursos | `domain`, `catalog`, `notation` |
| `numerics` | Avaliação da árvore em dupla precisão, malha, Hamiltoniano tridiagonal e falhas | `domain`, NumPy |
| `solvers/quadrature`, `solvers/ode`, `solvers/quantum` | Um método homologado por arquivo | `domain`, `numerics`, NumPy, SciPy |
| `verification/numerical` | Um verificador por família, sem importar os solvers | `domain`, `numerics`, NumPy, SciPy |

Regras cobradas por teste:

- NumPy e SciPy só aparecem em `numerics`, `solvers`, `verification` e no manifesto de ambiente. `application` não importa solver nem verificador.
- Todo método de ficha numérica tem solver e verificador registrados, e o exemplo de cada ficha é resolvido e verificado.
- Cada caso de referência concorda com um oráculo independente na tolerância do roadmap; o caso sub-resolvido não sai aprovado.
- A evidência registrada é reproduzida com tolerância numérica, nunca por igualdade bit a bit: 1e-6 do valor ou 1e-9 da maior magnitude registrada na mesma unidade.
- Recusa por perfil não inicia processo de cálculo; não convergência, limite de tempo e cancelamento não deixam resposta nem processo.

## O que ficou de fora

Rigidez. Potenciais além do nulo e do harmônico. Hamiltoniano dependente do tempo, estados mistos e medições generalizadas. Propagação de incerteza experimental nas fichas numéricas, que sai como não avaliada. Erro de malha na evolução temporal: a ficha mede só o erro no tempo. `adapters/storage`, `interfaces/api` e `web` continuam sem existir.

## Quando rever

Se um caso pedir potencial dado por expressão, com teste próprio de regularidade. Se o perfil homologado ficar pequeno, depois de medido no benchmark da fase 5. Se um problema rígido entrar no escopo, com método implícito e testes próprios.
