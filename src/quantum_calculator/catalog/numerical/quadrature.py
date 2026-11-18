from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.numerical.cards import InputSection, NumericalCard, NumericalFamily

ADAPTIVE_QUADRATURE = NumericalCard(
    identifier="calculus.definite_integral.adaptive_quadrature",
    version="1.0.0",
    area="differential_integral_calculus",
    problem_type="numerical_definite_integral",
    title="Aproximação de uma integral definida por quadratura adaptativa",
    domain=(
        "Integrando real explícito, escrito com as operações e funções registradas, finito em "
        "todo o intervalo fechado.",
        "Intervalo finito; todo parâmetro do integrando e dos limites tem valor numérico.",
    ),
    family=NumericalFamily.QUADRATURE,
    required_sections=frozenset(
        {InputSection.NOTATION, InputSection.SYMBOLS, InputSection.STATEMENT}
    ),
    optional_sections=frozenset({InputSection.REQUESTED}),
    hypotheses=(),
    quantities=(),
    method=MethodDescription(
        identifier="numerical.adaptive_quadrature",
        nature=ResultNature.APPROXIMATE,
        justification=(
            "O QUADPACK subdivide o intervalo onde o integrando varia mais, com regras de "
            "Gauss-Kronrod, e devolve o valor e uma estimativa de erro; a resposta é "
            "aproximada, dentro das tolerâncias pedidas."
        ),
        covariance_models=(),
    ),
    limitations=(
        "A resposta é aproximada. A estimativa do integrador não é uma cota demonstrada nem "
        "uma incerteza experimental.",
        "Um integrando não finito no intervalo ou que o limite de subdivisões não resolve "
        "termina sem resposta aprovada; integrais impróprias não são cobertas.",
        "A tolerância absoluta vale na unidade coerente do SI do resultado.",
    ),
    example="reference_cases/numerical/sine_quadrature.json",
)
