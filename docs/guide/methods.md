# Métodos

O que cada ficha calcula, por qual método, como a resposta é verificada e contra que oráculo a ficha foi homologada. `qcalc catalog` lista as mesmas 13 fichas com domínio e limitações. A matriz `case_matrix.json`, na raiz da distribuição, traz o valor esperado, a tolerância e o valor observado de cada um dos 111 casos.

Duas regras valem para todas as fichas. O verificador não usa a saída interna do solver como valor esperado: refaz a conta por outro caminho ou confere uma propriedade que a resposta precisa ter. E o oráculo da homologação é uma expressão fechada ou uma conta registrada em `reference_cases/`, não a saída de outro método da calculadora.

Os nomes entre crases depois de "Verificação" são os identificadores que aparecem no resultado.

## Expressão fechada

### `quantum.infinite_square_well.energy_level`

Nível de energia de uma partícula em um poço infinito unidimensional, por E_n = n^2 h^2 / (8 m L^2), em aritmética exata até a exibição.

Verificação: dimensão do resultado (`dimensional_consistency`); substituição de psi_n = sin(n pi x / L) na equação de Schrödinger (`stationary_schrodinger_residual`), anulamento nas extremidades (`dirichlet_boundary`) e normalização (`normalizable_mode`), as três por demonstração simbólica. A comparação com uma solução discreta fica a cargo da ficha `quantum.infinite_square_well.discrete_spectrum` e aparece aqui como não realizada.

Homologação: E_1 = 0.3760301621 eV para o elétron em 1 nm, com tolerância de 1e-9 eV, derivado em `reference_cases/quantum/electron_box_1nm.derivation.md`; e u(E) = 0.0075 eV para u(L) = 0.01 nm e u(m) = 2.8e-40 kg.

## Enunciado digitado

As seis fichas abaixo leem um enunciado em texto ou LaTeX e respondem em forma fechada. A resposta lista onde vale, as hipóteses que o domínio declarado não confirma e os casos especiais.

### `calculus.derivative`

Derivada ordinária ou parcial de uma expressão explícita, pelas regras de derivação das operações registradas.

Verificação: a derivada é refeita regra a regra (`rule_by_rule_derivative`), o domínio declarado é conferido contra as exclusões da expressão (`declared_domain_suffices`) e a dimensão é conferida (`dimensional_consistency`).

Homologação: d/dx de x^2 sin(x) = x^2 cos(x) + 2 x sin(x), comparada por equivalência matemática.

### `calculus.antiderivative`

Primitiva de uma expressão em uma variável, aceita só quando se escreve com as operações registradas. A resposta traz a constante de integração.

Verificação: a primitiva é derivada de volta e comparada com o integrando (`primitive_derivative`); o domínio é conferido (`declared_domain_suffices`).

Homologação: a primitiva de 1/x é ln|x| + C, fora de x = 0. `exp(-x^2)`, cuja primitiva pede a função erro, é recusada.

### `calculus.definite_integral`

Integral definida em intervalo finito, pelo teorema fundamental do cálculo, quando há primitiva contínua em todo o intervalo fechado.

Verificação: `primitive_derivative`, ausência de singularidade no intervalo (`interval_free_of_singularities`), valor pela diferença da primitiva (`fundamental_theorem_value`) e dimensão.

Homologação: a integral de x^2 em [0, 1] é 1/3. A integral de 1/x através de x = 0 é recusada.

### `ode.first_order_linear.general_solution`

Solução geral de uma EDO escalar, linear, de primeira ordem, com coeficientes constantes. Quando o domínio declarado não fixa o sinal do coeficiente de y, a resposta sai `conditional` e o caso de coeficiente nulo é listado à parte.

Verificação: a solução é substituída na equação (`equation_residual`) e o domínio é conferido.

Homologação: y' = -k y tem solução C exp(-k t). Uma equação não linear é recusada.

### `ode.first_order_linear.initial_value`

A mesma equação com uma condição inicial y(t0) = y0.

Verificação: `equation_residual`, a condição inicial (`initial_condition`), domínio e dimensão.

Homologação: y' = -k y com y(0) = y_0 dá y_0 exp(-k t).

### `ode.first_order_linear.candidate_review`

Revisão de uma solução candidata. A candidata é substituída na equação e a condição inicial é conferida à parte, então os dois motivos de reprovação saem separados.

Verificação: `equation_residual` e `initial_condition`, por demonstração; domínio e dimensão. Uma identidade que a simplificação não demonstra fica `inconclusive`.

Homologação: três candidatas para y' = -k y, y(0) = y_0. A correta é aprovada; `2*y_0*exp(-k*t)` é reprovada em `initial_condition`; `y_0*exp(k*t)` é reprovada em `equation_residual`.

## Métodos numéricos

A resolução vem escrita no bloco `numerics`. A resposta é `approximate` e cada grandeza sai com o erro estimado e a origem dele.

### `calculus.definite_integral.adaptive_quadrature`

Integral definida por quadratura adaptativa do QUADPACK. Ajustes: `absolute_tolerance`, `relative_tolerance`, `subdivision_limit`.

Verificação: a estimativa de erro do integrador é comparada com as tolerâncias pedidas (`integrator_error_estimate`) e a integral é refeita por Gauss-Legendre composto (`independent_quadrature`). A comparação com uma primitiva fechada não é feita.

Homologação: a integral de sin(x) em [0, pi] é 2, com tolerância de 1e-10. Uma integral divergente termina com código 9.

### `ode.initial_value.explicit_runge_kutta`

Trajetória de um sistema explícito, não rígido, de até oito componentes, por DOP853. Ajustes: `end`, `samples`, `relative_tolerance`, `absolute_tolerance`.

Verificação: a condição inicial é conferida na primeira amostra (`initial_condition`) e a trajetória é refeita com tolerâncias mais apertadas (`tolerance_refinement`). A rigidez não é diagnosticada e não há comparação com solução fechada.

Homologação: y' = -k y com k = 1/s e y(0) = 1 dá y(5 s) = exp(-5) = 0.006737946999085467, com tolerância de 1e-8. Uma trajetória que explode em tempo finito é recusada.

### `quantum.finite_basis.projective_measurement`

Probabilidades e valor esperado de um observável hermitiano em um estado puro de até 16 amplitudes, por decomposição espectral. Ajuste: `tolerance`.

Verificação: hermiticidade (`hermitian_operator`), norma do estado (`normalized_state`), soma das probabilidades (`total_probability`), projetores de subespaço construídos do observável, sem os autovetores do solver (`subspace_projectors`), valor esperado direto (`direct_expectation_value`) e invariância por fase global (`global_phase_invariance`).

Homologação: spin 1/2 no estado +x medido em sigma_z dá 1/2 e 1/2, com valor esperado 0; o mesmo estado com fase global i e em outra base dá as mesmas probabilidades; e um observável degenerado com o estado (1, 1, 1)/sqrt(3) dá P(1) = 2/3 e P(-1) = 1/3. Tolerância de 1e-12.

### `quantum.infinite_square_well.discrete_spectrum`

Primeiros níveis e autofunções do poço infinito, por diferenças centrais de segunda ordem em malha uniforme. O Hamiltoniano é guardado como duas diagonais e os níveis saem de `scipy.linalg.eigh_tridiagonal`, selecionados por índice, sem matriz densa. Ajustes: `subintervals`, `levels`.

Verificação: resíduo do operador discreto (`discrete_residual`), ortonormalidade na malha (`weighted_orthonormality`), extremos nulos (`dirichlet_boundary`), contagem de autovalores abaixo de cada nível (`level_placement`), refinamento com um quarto e com a metade da malha (`mesh_refinement`) e comparação com a expressão fechada (`closed_form_agreement`). Fora da ordem observada entre 1,8 e 2,2 a malha não é declarada convergida.

Homologação: com 512 subintervalos, E_1, E_2 e E_3 do elétron em 1 nm concordam com n^2 E_1 dentro de 3e-5 do valor. Com 16 subintervalos o resultado sai `inconclusive` em `mesh_refinement`.

### `quantum.harmonic_oscillator.truncated_spectrum`

Níveis e autofunções do oscilador harmônico em um domínio simétrico truncado, pelo mesmo método. Ajustes: `subintervals`, `levels`, `half_width`, em comprimentos do oscilador.

Verificação: as mesmas checagens do poço e o corte do domínio (`domain_truncation`), medido ampliando o domínio com o mesmo espaçamento. Refinar a malha e ampliar o domínio são experimentos separados.

Homologação: com hbar omega = 1 eV, os três primeiros níveis são 0,5, 1,5 e 2,5 eV, dentro de 1e-3 do valor. Com meia largura 3 o resultado sai `failed` em `closed_form_agreement` e `domain_truncation`: as paredes comprimem os estados.

### `quantum.infinite_square_well.time_evolution`

Evolução de uma superposição de até 16 modos discretos do poço, por Crank-Nicolson. O sistema tridiagonal complexo é fatorado uma vez e reutilizado em todos os passos, sem inversa explícita e sem renormalizar o estado. Ajustes: `subintervals`, `steps`, `samples`.

Verificação: conservação da norma (`norm_conservation`), integral da densidade final (`final_density_integral`), fase relativa contra a evolução exata dos modos discretos (`relative_phase`), dispersão prevista para o esquema (`scheme_dispersion`) e ordem temporal (`temporal_order`). O erro da malha espacial não é avaliado por esta ficha.

Homologação: no batimento dos dois primeiros estados do elétron em 1 nm, a deriva da norma fica abaixo de 1e-9 e o erro de fase abaixo de 1e-3 rad.
