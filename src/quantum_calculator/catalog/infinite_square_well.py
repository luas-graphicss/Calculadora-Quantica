from quantum_calculator.domain.cards import (
    HypothesisRule,
    OutputRule,
    PositiveIntegerRule,
    PositiveQuantityRule,
    ProblemCard,
)
from quantum_calculator.domain.dimensions import ENERGY, LENGTH, MASS
from quantum_calculator.domain.methods import (
    INDEPENDENT_COVARIANCE,
    MethodDescription,
    ResultNature,
)

INFINITE_SQUARE_WELL_ENERGY_LEVEL = ProblemCard(
    identifier="quantum.infinite_square_well.energy_level",
    version="1.0.0",
    area="stationary_schrodinger_1d",
    problem_type="energy_level",
    title="Nível de energia de uma partícula em um poço infinito unidimensional",
    domain=(
        "Massa e largura estritamente positivas e índice de nível inteiro positivo.",
        "Posição no intervalo aberto 0 < x < L.",
    ),
    scope=(
        "Partícula única, não relativística e sem spin, em uma dimensão espacial.",
        "Equação de Schrödinger independente do tempo no intervalo 0 < x < L.",
    ),
    quantities=(
        PositiveQuantityRule(name="mass", symbol="m", label="massa da partícula", dimension=MASS),
        PositiveQuantityRule(name="width", symbol="L", label="largura do poço", dimension=LENGTH),
    ),
    counts=(PositiveIntegerRule(name="level", symbol="n", label="índice do nível"),),
    hypotheses=(
        HypothesisRule(
            key="walls",
            required_value="infinite",
            statement="As paredes do poço são infinitas: a partícula não sai do intervalo.",
        ),
        HypothesisRule(
            key="interior_potential",
            required_value="zero",
            statement=(
                "O potencial dentro do poço é nulo, o que põe o zero de energia no fundo do poço."
            ),
        ),
        HypothesisRule(
            key="boundary_wavefunction",
            required_value="zero",
            statement="A função de onda se anula nas duas extremidades (Dirichlet homogênea).",
        ),
    ),
    outputs=(
        OutputRule(quantity="energy", symbol="E", label="energia do nível", dimension=ENERGY),
    ),
    method=MethodDescription(
        identifier="closed_form.infinite_square_well_energy",
        nature=ResultNature.EXACT,
        justification=(
            "O problema de autovalores com extremos de Dirichlet tem solução fechada, "
            "E_n = n^2 h^2 / (8 m L^2); nenhuma aproximação numérica é necessária."
        ),
        covariance_models=(INDEPENDENT_COVARIANCE,),
    ),
    limitations=(
        "Um poço finito, uma massa efetiva ou outro zero de energia definem problemas "
        "diferentes desta ficha.",
        "A expressão é exata no modelo; os algarismos exibidos não declaram a precisão "
        "experimental dos parâmetros.",
        "O modelo não relativístico perde validade quando a energia se aproxima de m c^2.",
    ),
    example="reference_cases/quantum/electron_box_1nm.json",
)
