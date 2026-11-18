from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.statement_cards import (
    StatementCard,
    StatementField,
    StatementShape,
)

_AREA = "ordinary_differential_equations"
_EQUATION_DOMAIN = (
    "Equação escalar de primeira ordem, linear na função incógnita e na sua derivada, com "
    "coeficientes e termo fonte que não dependem da variável independente."
)
_OUTSIDE_THE_FAMILY = (
    "Equações não lineares, de ordem maior, com coeficientes variáveis ou sistemas ficam "
    "fora desta ficha."
)
_CLOSED_FORM = MethodDescription(
    identifier="closed_form.first_order_linear_ode",
    nature=ResultNature.EXACT,
    justification=(
        "Para y' = a y + b com a e b constantes a solução é fechada: exponencial em torno "
        "do equilíbrio -b/a quando a é diferente de zero, e reta quando a é zero."
    ),
    covariance_models=(),
)

GENERAL_SOLUTION = StatementCard(
    identifier="ode.first_order_linear.general_solution",
    version="1.0.0",
    area=_AREA,
    problem_type="general_solution",
    title="Solução geral de uma EDO linear de primeira ordem com coeficientes constantes",
    domain=(_EQUATION_DOMAIN, "A família de soluções traz uma constante arbitrária."),
    shape=StatementShape.FIRST_ORDER_ODE,
    required_fields=frozenset(),
    method=_CLOSED_FORM,
    limitations=(
        _OUTSIDE_THE_FAMILY,
        "Se o sinal do coeficiente de y não está fixado pelo domínio declarado, a resposta "
        "é condicional e o caso de coeficiente nulo é listado à parte.",
    ),
    example="reference_cases/symbolic/decay_general_solution.json",
)

INITIAL_VALUE = StatementCard(
    identifier="ode.first_order_linear.initial_value",
    version="1.0.0",
    area=_AREA,
    problem_type="initial_value_problem",
    title="Problema de valor inicial de uma EDO linear de primeira ordem",
    domain=(_EQUATION_DOMAIN, "Uma condição inicial da forma y(t0) = y0."),
    shape=StatementShape.FIRST_ORDER_ODE,
    required_fields=frozenset({StatementField.CONDITIONS}),
    method=_CLOSED_FORM,
    limitations=(
        _OUTSIDE_THE_FAMILY,
        "A condição inicial é exigida: sem ela o problema é o da solução geral.",
    ),
    example="reference_cases/symbolic/decay_initial_value.json",
)

CANDIDATE_REVIEW = StatementCard(
    identifier="ode.first_order_linear.candidate_review",
    version="1.0.0",
    area=_AREA,
    problem_type="candidate_review",
    title="Revisão de uma solução candidata de um problema de valor inicial",
    domain=(
        _EQUATION_DOMAIN,
        "Uma condição inicial da forma y(t0) = y0 e uma candidata explícita y(t) = ...",
    ),
    shape=StatementShape.FIRST_ORDER_ODE,
    required_fields=frozenset({StatementField.CONDITIONS, StatementField.CANDIDATE}),
    method=MethodDescription(
        identifier="substitution.candidate_review",
        nature=ResultNature.EXACT,
        justification=(
            "A candidata é substituída na equação original e a condição inicial é conferida "
            "à parte; a equação não é resolvida."
        ),
        covariance_models=(),
    ),
    limitations=(
        _OUTSIDE_THE_FAMILY,
        "Concordância em pontos amostrados não é relatada como prova: sem demonstração, o "
        "resultado é inconclusivo.",
    ),
    example="reference_cases/symbolic/decay_candidate_correct.json",
)
