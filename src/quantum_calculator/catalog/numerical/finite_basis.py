from quantum_calculator.domain.cards import HypothesisRule
from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.numerical.cards import InputSection, NumericalCard, NumericalFamily

PROJECTIVE_MEASUREMENT = NumericalCard(
    identifier="quantum.finite_basis.projective_measurement",
    version="1.0.0",
    area="finite_basis_quantum_mechanics",
    problem_type="projective_measurement",
    title="Medição projetiva de um observável em um estado puro de base finita",
    domain=(
        "Estado puro dado por até 16 amplitudes complexas em uma base ortonormal.",
        "Observável hermitiano dado pela matriz na mesma base; uma mudança para outra base "
        "ortonormal é opcional.",
    ),
    family=NumericalFamily.FINITE_BASIS,
    required_sections=frozenset(
        {InputSection.HYPOTHESES, InputSection.STATE, InputSection.OBSERVABLE}
    ),
    optional_sections=frozenset({InputSection.BASIS, InputSection.REQUESTED}),
    hypotheses=(
        HypothesisRule(
            key="state",
            required_value="pure",
            statement="O estado é puro: um vetor de amplitudes, não uma matriz densidade.",
        ),
        HypothesisRule(
            key="measurement",
            required_value="projective",
            statement="A medição é projetiva, sobre os autoespaços do observável.",
        ),
    ),
    quantities=(),
    method=MethodDescription(
        identifier="numerical.hermitian_eigendecomposition",
        nature=ResultNature.APPROXIMATE,
        justification=(
            "A matriz hermitiana é diagonalizada em dupla precisão e cada probabilidade é a "
            "norma da projeção do estado no autoespaço do autovalor; forma, norma, base e "
            "hermiticidade são conferidas antes."
        ),
        covariance_models=(),
    ),
    limitations=(
        "Estados mistos, medições generalizadas e evolução temporal ficam fora desta ficha.",
        "Autovalores mais próximos que a tolerância são tratados como um único subespaço.",
        "As amplitudes entram como números: uma raiz quadrada vem como decimal ou com a "
        "normalização pedida, que fica registrada.",
    ),
    example="reference_cases/numerical/spin_half_measurement.json",
)
