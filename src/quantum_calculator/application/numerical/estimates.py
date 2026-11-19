from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.numerical.problems import ResourceEstimate

MAX_MEMORY_BYTES = 256 * 1024**2
MAX_OPERATIONS = 2_000_000_000

_DOUBLE = 8
_COMPLEX = 16
_QUADRATURE_WORK_ARRAYS = 8
_QUADRATURE_NODES = 21
_RUNGE_KUTTA_STAGES = 12
_TRAJECTORY_COPIES = 3
_EIGENVECTOR_WORK = 12
_EIGENSOLVER_SWEEPS = 200
_PROPAGATION_VECTORS = 12
_STEP_OPERATIONS = 12
_REFINEMENT_RUNS = (7, 4)
_DENSE_WORK_MATRICES = 8
_DENSE_EIGENSOLVER_FACTOR = 30
_OBSERVABLE_COLUMNS = 6
_WIDENED_DOMAIN = (9, 4)


def quadrature_estimate(subdivisions: int, integrand_nodes: int) -> ResourceEstimate:
    return ResourceEstimate(
        memory_bytes=_DOUBLE * _QUADRATURE_WORK_ARRAYS * subdivisions,
        operations=_QUADRATURE_NODES * subdivisions * integrand_nodes,
    )


def initial_value_estimate(
    samples: int, components: int, derivative_nodes: int
) -> ResourceEstimate:
    return ResourceEstimate(
        memory_bytes=_DOUBLE * _TRAJECTORY_COPIES * samples * (components + 1),
        operations=_RUNGE_KUTTA_STAGES * samples * derivative_nodes,
    )


def finite_basis_estimate(dimension: int) -> ResourceEstimate:
    return ResourceEstimate(
        memory_bytes=_COMPLEX * _DENSE_WORK_MATRICES * dimension**2,
        operations=_DENSE_EIGENSOLVER_FACTOR * dimension**3,
    )


def spectrum_estimate(subintervals: int, levels: int, *, is_truncated: bool) -> ResourceEstimate:
    numerator, denominator = _WIDENED_DOMAIN if is_truncated else (1, 1)
    unknowns = subintervals * numerator // denominator
    return ResourceEstimate(
        memory_bytes=_DOUBLE * unknowns * (2 * levels + _EIGENVECTOR_WORK),
        operations=_EIGENSOLVER_SWEEPS * unknowns * levels,
    )


def evolution_estimate(subintervals: int, modes: int, steps: int, samples: int) -> ResourceEstimate:
    numerator, denominator = _REFINEMENT_RUNS
    return ResourceEstimate(
        memory_bytes=_COMPLEX * subintervals * (modes + _PROPAGATION_VECTORS)
        + _DOUBLE * samples * (modes + _OBSERVABLE_COLUMNS),
        operations=_STEP_OPERATIONS * subintervals * steps * numerator // denominator
        + _EIGENSOLVER_SWEEPS * subintervals * modes,
    )


def check_profile(request: ValidationRequest, estimate: ResourceEstimate) -> None:
    if estimate.memory_bytes > MAX_MEMORY_BYTES or estimate.operations > MAX_OPERATIONS:
        request.refuse(
            DiagnosticCode.RESOURCE_LIMIT_EXCEEDED,
            pointer_to("numerics"),
            f"O pedido estima {estimate.memory_bytes} bytes de memória e {estimate.operations} "
            "operações elementares, acima do perfil homologado. Nada foi alocado.",
            f"um pedido de até {MAX_MEMORY_BYTES} bytes e {MAX_OPERATIONS} operações estimadas",
        )
