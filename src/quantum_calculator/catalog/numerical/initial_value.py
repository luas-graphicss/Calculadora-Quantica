from quantum_calculator.domain.methods import MethodDescription, ResultNature
from quantum_calculator.domain.numerical.cards import InputSection, NumericalCard, NumericalFamily

EXPLICIT_RUNGE_KUTTA = NumericalCard(
    identifier="ode.initial_value.explicit_runge_kutta",
    version="1.0.0",
    area="ordinary_differential_equations",
    problem_type="numerical_initial_value_problem",
    title="Trajetória de um problema de valor inicial explícito e não rígido",
    domain=(
        "Uma equação de primeira ordem por função incógnita, na forma y' = f(t, y, ...), com "
        "lado direito explícito e suave; sistemas de até oito componentes.",
        "Uma condição inicial por função, todas no mesmo instante, e todo parâmetro com valor "
        "numérico.",
    ),
    family=NumericalFamily.INITIAL_VALUE,
    required_sections=frozenset(
        {
            InputSection.NOTATION,
            InputSection.SYMBOLS,
            InputSection.EQUATIONS,
            InputSection.CONDITIONS,
        }
    ),
    optional_sections=frozenset({InputSection.REQUESTED}),
    hypotheses=(),
    quantities=(),
    method=MethodDescription(
        identifier="numerical.dop853",
        nature=ResultNature.APPROXIMATE,
        justification=(
            "O DOP853 é um método de Runge-Kutta explícito de ordem 8 com passo adaptativo, "
            "adequado a problemas suaves e não rígidos; a trajetória é aproximada, dentro "
            "das tolerâncias pedidas por passo."
        ),
        covariance_models=(),
    ),
    limitations=(
        "A rigidez não é diagnosticada nem tratada: um problema rígido esgota o passo ou o "
        "orçamento e termina sem resposta aprovada.",
        "As tolerâncias controlam o erro local de cada passo; o erro acumulado é conferido "
        "por refinamento, não demonstrado.",
        "A tolerância absoluta vale na unidade coerente do SI de cada componente.",
    ),
    example="reference_cases/numerical/decay_trajectory.json",
)
