import sympy

from quantum_calculator.solvers.symbolic.results import outside_coverage

_NO_NUMERICAL_METHOD = (
    "um integrando com primitiva nas operações registradas; nenhum método numérico está "
    "homologado nesta versão"
)


def find_primitive(integrand: sympy.Expr, variable: sympy.Symbol) -> sympy.Expr:
    primitive = sympy.integrate(integrand, variable)
    if primitive.has(sympy.Integral):
        raise outside_coverage(
            "Não foi encontrada primitiva em forma fechada para o integrando.",
            _NO_NUMERICAL_METHOD,
        )
    introduced = primitive.atoms(sympy.log) - integrand.atoms(sympy.log)
    return primitive.xreplace(
        {logarithm: sympy.log(sympy.Abs(logarithm.args[0])) for logarithm in introduced}
    )
