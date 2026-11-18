from quantum_calculator.domain.cards import HypothesisRule, PositiveQuantityRule
from quantum_calculator.domain.dimensions import ENERGY, LENGTH, MASS, TIME
from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.numerical.cards import InputSection, NumericalCard, NumericalFamily

_DIRICHLET = HypothesisRule(
    key="boundary_wavefunction",
    required_value="zero",
    statement="A função de onda se anula nas duas extremidades (Dirichlet homogênea).",
)
_INFINITE_WALLS = HypothesisRule(
    key="walls",
    required_value="infinite",
    statement="As paredes do poço são infinitas: a partícula não sai do intervalo.",
)
_FLAT_INTERIOR = HypothesisRule(
    key="interior_potential",
    required_value="zero",
    statement="O potencial dentro do poço é nulo, o que põe o zero de energia no fundo do poço.",
)
_MASS = PositiveQuantityRule(name="mass", symbol="m", label="massa da partícula", dimension=MASS)
_WIDTH = PositiveQuantityRule(name="width", symbol="L", label="largura do poço", dimension=LENGTH)
_SINGLE_PARTICLE = "Partícula única, não relativística e sem spin, em uma dimensão espacial."
_FINITE_DIFFERENCES = MethodDescription(
    identifier="finite_difference.tridiagonal_eigensolver",
    nature=ResultNature.APPROXIMATE,
    justification=(
        "O Hamiltoniano é discretizado por diferenças centrais de segunda ordem nos nós "
        "internos de uma malha uniforme; os níveis pedidos saem das diagonais, sem matriz "
        "densa, e o erro de malha é estimado por refinamento."
    ),
    covariance_models=(),
)
_MESH_ERROR = (
    "A resposta é aproximada: o erro de malha cai com o quadrado do espaçamento e só é "
    "declarado convergido quando o refinamento mostra a ordem esperada."
)
_NO_UNCERTAINTY = (
    "Incertezas dos parâmetros não são propagadas por esta ficha: a incerteza experimental "
    "fica não avaliada."
)

WELL_DISCRETE_SPECTRUM = NumericalCard(
    identifier="quantum.infinite_square_well.discrete_spectrum",
    version="1.0.0",
    area="stationary_schrodinger_1d",
    problem_type="discrete_spectrum",
    title="Níveis e autofunções do poço infinito por diferenças finitas",
    domain=(
        _SINGLE_PARTICLE,
        "Massa e largura estritamente positivas; os primeiros níveis, até 32, em uma malha "
        "uniforme de até 16384 subintervalos.",
    ),
    family=NumericalFamily.WELL_SPECTRUM,
    required_sections=frozenset(
        {InputSection.HYPOTHESES, InputSection.PARAMETERS, InputSection.REQUESTED}
    ),
    optional_sections=frozenset(),
    hypotheses=(_INFINITE_WALLS, _FLAT_INTERIOR, _DIRICHLET),
    quantities=(_MASS, _WIDTH),
    method=_FINITE_DIFFERENCES,
    limitations=(
        _MESH_ERROR,
        "A expressão fechada do poço, da ficha quantum.infinite_square_well.energy_level, é "
        "usada só como referência independente na verificação.",
        _NO_UNCERTAINTY,
    ),
    example="reference_cases/numerical/electron_box_1nm_discrete.json",
)

OSCILLATOR_TRUNCATED_SPECTRUM = NumericalCard(
    identifier="quantum.harmonic_oscillator.truncated_spectrum",
    version="1.0.0",
    area="stationary_schrodinger_1d",
    problem_type="truncated_spectrum",
    title="Níveis e autofunções do oscilador harmônico em domínio truncado",
    domain=(
        _SINGLE_PARTICLE,
        "Massa e quantum de energia hbar omega estritamente positivos; domínio simétrico de "
        "meia largura dada em comprimentos do oscilador, sqrt(hbar / (m omega)).",
    ),
    family=NumericalFamily.OSCILLATOR_SPECTRUM,
    required_sections=frozenset(
        {InputSection.HYPOTHESES, InputSection.PARAMETERS, InputSection.REQUESTED}
    ),
    optional_sections=frozenset(),
    hypotheses=(
        HypothesisRule(
            key="potential",
            required_value="harmonic",
            statement="O potencial é m omega^2 x^2 / 2, centrado no meio do domínio.",
        ),
        HypothesisRule(
            key="domain",
            required_value="truncated",
            statement=(
                "O domínio infinito é truncado em um intervalo simétrico: os níveis valem "
                "enquanto a função de onda for desprezível nos extremos."
            ),
        ),
        _DIRICHLET,
    ),
    quantities=(
        _MASS,
        PositiveQuantityRule(
            name="level_spacing",
            symbol="hbar omega",
            label="quantum de energia do oscilador",
            dimension=ENERGY,
        ),
    ),
    method=_FINITE_DIFFERENCES,
    limitations=(
        _MESH_ERROR,
        "Ampliar o domínio e refinar a malha são experimentos separados: o primeiro mede o "
        "corte do domínio, o segundo o erro de discretização.",
        _NO_UNCERTAINTY,
    ),
    example="reference_cases/numerical/harmonic_oscillator_1ev.json",
)

WELL_TIME_EVOLUTION = NumericalCard(
    identifier="quantum.infinite_square_well.time_evolution",
    version="1.0.0",
    area="time_dependent_schrodinger_1d",
    problem_type="time_evolution",
    title="Evolução de uma superposição de estados do poço infinito por Crank-Nicolson",
    domain=(
        _SINGLE_PARTICLE,
        "Estado inicial dado por até 16 coeficientes complexos sobre os primeiros modos "
        "discretos do poço; duração positiva dividida em passos iguais.",
    ),
    family=NumericalFamily.WELL_EVOLUTION,
    required_sections=frozenset(
        {InputSection.HYPOTHESES, InputSection.PARAMETERS, InputSection.INITIAL_STATE}
    ),
    optional_sections=frozenset({InputSection.REQUESTED}),
    hypotheses=(
        _INFINITE_WALLS,
        _FLAT_INTERIOR,
        _DIRICHLET,
        HypothesisRule(
            key="hamiltonian",
            required_value="time_independent",
            statement="O Hamiltoniano não depende do tempo e a evolução é fechada.",
        ),
    ),
    quantities=(
        _MASS,
        _WIDTH,
        PositiveQuantityRule(
            name="duration", symbol="T", label="duração da evolução", dimension=TIME
        ),
    ),
    method=MethodDescription(
        identifier="finite_difference.crank_nicolson",
        nature=ResultNature.APPROXIMATE,
        justification=(
            "O esquema de Crank-Nicolson é unitário e de segunda ordem no tempo; o sistema "
            "tridiagonal é fatorado uma vez e reutilizado em todos os passos, sem inversa "
            "explícita e sem renormalizar o estado."
        ),
        covariance_models=(),
    ),
    limitations=(
        "A resposta é aproximada. A verificação mede o erro temporal contra a evolução exata "
        "dos modos discretos; o erro da malha não é avaliado aqui.",
        "Norma e fase estáveis em uma animação não comprovam precisão temporal: valem as "
        "checagens de norma, de fase e de ordem.",
        "Só os observáveis dos instantes salvos e a densidade final são guardados.",
    ),
    example="reference_cases/numerical/electron_box_1nm_beat.json",
)
