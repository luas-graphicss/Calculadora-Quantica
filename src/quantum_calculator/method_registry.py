from quantum_calculator.application.solve_numerical import HomologatedNumericalMethod
from quantum_calculator.application.solve_problem import HomologatedMethod
from quantum_calculator.application.solve_statement import HomologatedStatementMethod
from quantum_calculator.catalog.calculus import ANTIDERIVATIVE, DEFINITE_INTEGRAL, DERIVATIVE
from quantum_calculator.catalog.first_order_linear_ode import CANDIDATE_REVIEW, GENERAL_SOLUTION
from quantum_calculator.catalog.infinite_square_well import INFINITE_SQUARE_WELL_ENERGY_LEVEL
from quantum_calculator.catalog.numerical.discrete_schrodinger import (
    WELL_DISCRETE_SPECTRUM,
    WELL_TIME_EVOLUTION,
)
from quantum_calculator.catalog.numerical.finite_basis import PROJECTIVE_MEASUREMENT
from quantum_calculator.catalog.numerical.initial_value import EXPLICIT_RUNGE_KUTTA
from quantum_calculator.catalog.numerical.quadrature import ADAPTIVE_QUADRATURE
from quantum_calculator.domain.ports import ConstantsEdition
from quantum_calculator.solvers.ode.explicit_runge_kutta import ExplicitRungeKuttaSolver
from quantum_calculator.solvers.quadrature.adaptive import AdaptiveQuadratureSolver
from quantum_calculator.solvers.quantum.evolution import CrankNicolsonEvolutionSolver
from quantum_calculator.solvers.quantum.finite_basis import ProjectiveMeasurementSolver
from quantum_calculator.solvers.quantum.stationary import TridiagonalSpectrumSolver
from quantum_calculator.solvers.symbolic.candidate import CandidateClaim
from quantum_calculator.solvers.symbolic.differentiation import DifferentiationSolver
from quantum_calculator.solvers.symbolic.first_order_linear_ode import FirstOrderLinearSolver
from quantum_calculator.solvers.symbolic.infinite_square_well import InfiniteSquareWellSolver
from quantum_calculator.solvers.symbolic.integration import (
    AntiderivativeSolver,
    DefiniteIntegralSolver,
)
from quantum_calculator.verification.differentiation import DifferentiationVerifier
from quantum_calculator.verification.infinite_square_well import InfiniteSquareWellVerifier
from quantum_calculator.verification.integration import (
    AntiderivativeVerifier,
    DefiniteIntegralVerifier,
)
from quantum_calculator.verification.numerical.evolution import EvolutionVerifier
from quantum_calculator.verification.numerical.finite_basis import FiniteBasisVerifier
from quantum_calculator.verification.numerical.initial_value import InitialValueVerifier
from quantum_calculator.verification.numerical.quadrature import QuadratureVerifier
from quantum_calculator.verification.numerical.spectrum import SpectrumVerifier
from quantum_calculator.verification.ode_substitution import OdeSubstitutionVerifier


def problem_methods(constants: ConstantsEdition) -> dict[str, HomologatedMethod]:
    return {
        INFINITE_SQUARE_WELL_ENERGY_LEVEL.method.identifier: HomologatedMethod(
            solver=InfiniteSquareWellSolver(constants),
            verifier=InfiniteSquareWellVerifier(constants),
        )
    }


def statement_methods() -> dict[str, HomologatedStatementMethod]:
    return {
        DERIVATIVE.method.identifier: HomologatedStatementMethod(
            DifferentiationSolver(), DifferentiationVerifier()
        ),
        ANTIDERIVATIVE.method.identifier: HomologatedStatementMethod(
            AntiderivativeSolver(), AntiderivativeVerifier()
        ),
        DEFINITE_INTEGRAL.method.identifier: HomologatedStatementMethod(
            DefiniteIntegralSolver(), DefiniteIntegralVerifier()
        ),
        GENERAL_SOLUTION.method.identifier: HomologatedStatementMethod(
            FirstOrderLinearSolver(), OdeSubstitutionVerifier()
        ),
        CANDIDATE_REVIEW.method.identifier: HomologatedStatementMethod(
            CandidateClaim(), OdeSubstitutionVerifier()
        ),
    }


def numerical_methods() -> dict[str, HomologatedNumericalMethod]:
    return {
        ADAPTIVE_QUADRATURE.method.identifier: HomologatedNumericalMethod(
            AdaptiveQuadratureSolver(), QuadratureVerifier()
        ),
        EXPLICIT_RUNGE_KUTTA.method.identifier: HomologatedNumericalMethod(
            ExplicitRungeKuttaSolver(), InitialValueVerifier()
        ),
        PROJECTIVE_MEASUREMENT.method.identifier: HomologatedNumericalMethod(
            ProjectiveMeasurementSolver(), FiniteBasisVerifier()
        ),
        WELL_DISCRETE_SPECTRUM.method.identifier: HomologatedNumericalMethod(
            TridiagonalSpectrumSolver(), SpectrumVerifier()
        ),
        WELL_TIME_EVOLUTION.method.identifier: HomologatedNumericalMethod(
            CrankNicolsonEvolutionSolver(), EvolutionVerifier()
        ),
    }
