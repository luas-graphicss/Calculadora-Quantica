from scipy import linalg

from quantum_calculator.numerics.failures import method_not_converged
from quantum_calculator.numerics.finite_basis import Amplitudes
from quantum_calculator.numerics.hamiltonian import TridiagonalOperator

FACTORIZATION = "LAPACK gttrf"

_FACTORED = 0


class CrankNicolsonPropagator:
    def __init__(self, operator: TridiagonalOperator, step: float) -> None:
        half_step = 0.5j * step
        self._explicit_diagonal = 1.0 - half_step * operator.diagonal
        self._explicit_coupling = -half_step * operator.off_diagonal
        implicit_diagonal = 1.0 + half_step * operator.diagonal
        implicit_coupling = half_step * operator.off_diagonal
        factorize, self._substitute = linalg.get_lapack_funcs(
            ("gttrf", "gttrs"), (implicit_diagonal,)
        )
        *self._factors, status = factorize(implicit_coupling, implicit_diagonal, implicit_coupling)
        if int(status) != _FACTORED:
            raise method_not_converged(
                FACTORIZATION, f"a fatoração do sistema implícito parou com info = {status}."
            )

    def advance(self, state: Amplitudes) -> Amplitudes:
        explicit = self._explicit_diagonal * state
        explicit[:-1] += self._explicit_coupling * state[1:]
        explicit[1:] += self._explicit_coupling * state[:-1]
        advanced: Amplitudes = self._substitute(*self._factors, explicit)[0]
        return advanced
