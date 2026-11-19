import sympy

from quantum_calculator.solvers.symbolic.results import outside_coverage

_CLOSED_FORM_OR_QUADRATURE = (
    "um integrando com primitiva nas operações registradas; uma integral definida sem ela é "
    "aproximada pela ficha calculus.definite_integral.adaptive_quadrature"
)


def find_primitive(integrand: sympy.Expr, variable: sympy.Symbol) -> sympy.Expr:
    primitive = sympy.integrate(integrand, variable)
    if primitive.has(sympy.Integral):
        raise outside_coverage(
            "Não foi encontrada primitiva em forma fechada para o integrando.",
            _CLOSED_FORM_OR_QUADRATURE,
        )
    introduced = primitive.atoms(sympy.log) - integrand.atoms(sympy.log)
    return primitive.xreplace(
        {logarithm: sympy.log(sympy.Abs(logarithm.args[0])) for logarithm in introduced}
    )
