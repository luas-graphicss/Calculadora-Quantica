from dataclasses import dataclass

import sympy
from sympy.core.function import AppliedUndef

from quantum_calculator.solvers.symbolic.results import outside_coverage

_LINEAR_CONSTANT_FORM = (
    "uma equação linear em y e y', com coeficientes e termo fonte que não dependem da "
    "variável independente"
)


@dataclass(frozen=True, slots=True)
class LinearForm:
    rate: sympy.Expr
    source: sympy.Expr


def linear_form(residual: sympy.Expr, unknown: sympy.Expr, variable: sympy.Symbol) -> LinearForm:
    slope = sympy.Dummy("slope")
    level = sympy.Dummy("level")
    replaced = residual.subs(sympy.Derivative(unknown, variable), slope).subs(unknown, level)
    if replaced.has(sympy.Derivative, AppliedUndef):
        raise outside_coverage(
            "A incógnita aparece fora do seu argumento declarado ou em outra derivada.",
            _LINEAR_CONSTANT_FORM,
        )
    try:
        polynomial = sympy.Poly(sympy.expand(replaced), slope, level)
    except sympy.PolynomialError as error:
        raise _nonlinear() from error
    if polynomial.total_degree() > 1:
        raise _nonlinear()
    leading = polynomial.coeff_monomial(slope)
    damping = polynomial.coeff_monomial(level)
    offset = polynomial.coeff_monomial(1)
    if any(variable in coefficient.free_symbols for coefficient in (leading, damping, offset)):
        raise outside_coverage(
            f"Os coeficientes ou o termo fonte dependem de {variable.name}.", _LINEAR_CONSTANT_FORM
        )
    if sympy.simplify(leading).is_zero:
        raise outside_coverage(
            "A derivada da incógnita se cancela: a equação não é diferencial.",
            _LINEAR_CONSTANT_FORM,
        )
    return LinearForm(
        rate=sympy.simplify(-damping / leading), source=sympy.simplify(-offset / leading)
    )


def _nonlinear() -> Exception:
    return outside_coverage(
        "A equação não é linear na incógnita e na sua derivada.", _LINEAR_CONSTANT_FORM
    )
