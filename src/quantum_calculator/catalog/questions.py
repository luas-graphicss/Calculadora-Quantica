from quantum_calculator.domain.workbench.questions import CardChoice, PhysicalQuestion

PHYSICAL_QUESTIONS = (
    PhysicalQuestion(
        identifier="confined_particle_energy",
        question="Qual é a energia de uma partícula confinada em um poço infinito?",
        context=(
            "Uma partícula em uma dimensão, entre paredes impenetráveis, com potencial nulo "
            "no interior."
        ),
        choices=(
            CardChoice(
                "quantum.infinite_square_well.energy_level",
                "Um nível escolhido, pela expressão fechada: resposta exata, com a incerteza "
                "propagada quando ela é declarada.",
            ),
            CardChoice(
                "quantum.infinite_square_well.discrete_spectrum",
                "Os primeiros níveis e as autofunções em uma malha: resposta aproximada, com o "
                "erro de malha estimado.",
            ),
        ),
    ),
    PhysicalQuestion(
        identifier="harmonic_oscillator_levels",
        question="Quais são os níveis e as autofunções de um oscilador harmônico?",
        context="Uma partícula em uma dimensão sob potencial quadrático.",
        choices=(
            CardChoice(
                "quantum.harmonic_oscillator.truncated_spectrum",
                "Os primeiros níveis e as autofunções em um domínio truncado: resposta "
                "aproximada, com o erro de malha e o do corte do domínio medidos em separado.",
            ),
        ),
    ),
    PhysicalQuestion(
        identifier="superposition_evolution",
        question="Como uma superposição de estados evolui no tempo dentro do poço?",
        context="Evolução fechada, com Hamiltoniano que não depende do tempo.",
        choices=(
            CardChoice(
                "quantum.infinite_square_well.time_evolution",
                "Norma, populações e fase relativa nos instantes salvos e a densidade final: "
                "resposta aproximada, com o erro temporal conferido.",
            ),
        ),
    ),
    PhysicalQuestion(
        identifier="measurement_outcomes",
        question="Que resultados uma medição pode dar, e com que probabilidade?",
        context="Um estado puro e um observável hermitiano escritos em uma base finita.",
        choices=(
            CardChoice(
                "quantum.finite_basis.projective_measurement",
                "Os autovalores, a probabilidade de cada um e o valor esperado do observável.",
            ),
        ),
    ),
    PhysicalQuestion(
        identifier="rate_of_change",
        question="Como uma grandeza varia quando outra muda?",
        context="Uma expressão explícita e a variável em relação à qual ela é derivada.",
        choices=(
            CardChoice(
                "calculus.derivative",
                "A derivada ordinária ou parcial, em forma fechada, com o domínio em que vale.",
            ),
        ),
    ),
    PhysicalQuestion(
        identifier="accumulated_quantity",
        question="Quanto uma grandeza acumula ao longo de um intervalo?",
        context="Uma expressão de uma variável, integrada entre limites ou sem eles.",
        choices=(
            CardChoice(
                "calculus.definite_integral",
                "O valor exato da integral em um intervalo, quando existe primitiva em forma "
                "fechada.",
            ),
            CardChoice(
                "calculus.antiderivative",
                "A primitiva da expressão, conferida por derivação.",
            ),
            CardChoice(
                "calculus.definite_integral.adaptive_quadrature",
                "Um valor aproximado da integral em um intervalo, com estimativa de erro, "
                "quando a forma fechada não existe ou não é necessária.",
            ),
        ),
    ),
    PhysicalQuestion(
        identifier="evolution_law",
        question="Que função obedece a esta lei de evolução?",
        context=(
            "Uma equação diferencial ordinária de primeira ordem e, se houver, o ponto de partida."
        ),
        choices=(
            CardChoice(
                "ode.first_order_linear.initial_value",
                "A solução exata que parte de uma condição inicial, para uma lei linear com "
                "coeficientes constantes.",
            ),
            CardChoice(
                "ode.first_order_linear.general_solution",
                "A família de soluções exatas da mesma lei, com a constante arbitrária.",
            ),
            CardChoice(
                "ode.initial_value.explicit_runge_kutta",
                "A trajetória aproximada de um sistema explícito e não rígido, da condição "
                "inicial até um instante final.",
            ),
        ),
    ),
    PhysicalQuestion(
        identifier="candidate_check",
        question="A solução que eu encontrei está correta?",
        context="Uma equação linear de primeira ordem, a condição inicial e a função candidata.",
        choices=(
            CardChoice(
                "ode.first_order_linear.candidate_review",
                "A candidata substituída na equação e a condição inicial conferida à parte: os "
                "dois motivos de reprovação saem separados.",
            ),
        ),
    ),
)
