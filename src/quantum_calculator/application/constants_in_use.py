from quantum_calculator.domain.constants import PhysicalConstant
from quantum_calculator.domain.ports import ConstantsEdition, require_constant
from quantum_calculator.domain.solution import SolverReport
from quantum_calculator.domain.validated_problem import ValidatedProblem


def constants_in_use(
    problem: ValidatedProblem, report: SolverReport, constants: ConstantsEdition
) -> tuple[PhysicalConstant, ...]:
    cited_by_parameters = (
        bound.origin for bound in problem.quantities if isinstance(bound.origin, PhysicalConstant)
    )
    defining_the_display_unit = (
        require_constant(constants, identifier)
        for identifier in problem.output.unit.defining_constants
    )
    used = (*report.constants, *cited_by_parameters, *defining_the_display_unit)
    return tuple({constant.identifier: constant for constant in used}.values())
