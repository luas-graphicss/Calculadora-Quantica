from quantum_calculator.application.solve_problem import HomologatedMethod
from quantum_calculator.application.solve_statement import HomologatedStatementMethod
from quantum_calculator.catalog.calculus import ANTIDERIVATIVE, DEFINITE_INTEGRAL, DERIVATIVE
from quantum_calculator.catalog.first_order_linear_ode import CANDIDATE_REVIEW, GENERAL_SOLUTION
from quantum_calculator.catalog.infinite_square_well import INFINITE_SQUARE_WELL_ENERGY_LEVEL
from quantum_calculator.domain.ports import ConstantsEdition
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
