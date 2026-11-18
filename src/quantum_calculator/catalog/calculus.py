from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.statement_cards import StatementCard, StatementShape

_AREA = "differential_integral_calculus"
_EXPLICIT_REAL_EXPRESSIONS = (
    "Expressões reais explícitas, escritas com as operações e funções registradas, sobre "
    "símbolos com domínio real declarado."
)
_NO_NUMERICAL_ALTERNATIVE = (
    "Nenhum método numérico está homologado nesta versão: sem primitiva coberta, nenhuma "
    "aproximação é oferecida."
)

DERIVATIVE = StatementCard(
    identifier="calculus.derivative",
    version="1.0.0",
    area=_AREA,
    problem_type="derivative",
    title="Derivada ordinária ou parcial de uma expressão explícita",
    domain=(
        _EXPLICIT_REAL_EXPRESSIONS,
        "O resultado vale onde a expressão e a derivada estão definidas; as exclusões são "
        "listadas com a resposta.",
    ),
    shape=StatementShape.DERIVATIVE,
    required_fields=frozenset(),
    method=MethodDescription(
        identifier="symbolic.differentiation",
        nature=ResultNature.EXACT,
        justification=(
            "As regras de derivação das operações e funções registradas dão a derivada em "
            "forma fechada; nenhuma aproximação numérica é necessária."
        ),
        covariance_models=(),
    ),
    limitations=(
        "Não deriva funções incógnitas, integrais nem derivadas aninhadas.",
        "A simplificação preserva as exclusões da expressão original: os zeros de um fator "
        "cancelado continuam fora do domínio.",
    ),
    example="reference_cases/symbolic/product_rule.json",
)

ANTIDERIVATIVE = StatementCard(
    identifier="calculus.antiderivative",
    version="1.0.0",
    area=_AREA,
    problem_type="antiderivative",
    title="Primitiva de uma expressão explícita em uma variável",
    domain=(
        _EXPLICIT_REAL_EXPRESSIONS,
        "A primitiva vale em cada intervalo em que o integrando está definido.",
    ),
    shape=StatementShape.ANTIDERIVATIVE,
    required_fields=frozenset(),
    method=MethodDescription(
        identifier="symbolic.antidifferentiation",
        nature=ResultNature.EXACT,
        justification=(
            "A primitiva é procurada em forma fechada e só é aceita quando se escreve com as "
            "operações registradas; a resposta traz a constante de integração."
        ),
        covariance_models=(),
    ),
    limitations=(
        "Integrandos cuja primitiva pede funções especiais, como erf ou a integral seno, "
        "ficam fora da cobertura.",
        _NO_NUMERICAL_ALTERNATIVE,
        "Quando o domínio tem exclusões, a constante de integração pode ser diferente em "
        "cada intervalo.",
    ),
    example="reference_cases/symbolic/reciprocal_primitive.json",
)

DEFINITE_INTEGRAL = StatementCard(
    identifier="calculus.definite_integral",
    version="1.0.0",
    area=_AREA,
    problem_type="definite_integral",
    title="Integral definida de uma expressão explícita em um intervalo finito",
    domain=(
        _EXPLICIT_REAL_EXPRESSIONS,
        "Intervalo finito, com o integrando definido e uma primitiva contínua em todo o "
        "intervalo fechado.",
    ),
    shape=StatementShape.DEFINITE_INTEGRAL,
    required_fields=frozenset(),
    method=MethodDescription(
        identifier="symbolic.fundamental_theorem",
        nature=ResultNature.EXACT,
        justification=(
            "Com uma primitiva contínua no intervalo fechado, o teorema fundamental do "
            "cálculo dá o valor exato como diferença da primitiva nos extremos."
        ),
        covariance_models=(),
    ),
    limitations=(
        "Uma singularidade do integrando ou da primitiva no intervalo fechado é recusada; "
        "integrais impróprias não são cobertas.",
        _NO_NUMERICAL_ALTERNATIVE,
    ),
    example="reference_cases/symbolic/parabola_area.json",
)
