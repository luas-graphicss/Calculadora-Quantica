from collections.abc import Mapping
from dataclasses import dataclass

from quantum_calculator.application.constants_in_use import constants_in_use
from quantum_calculator.application.planning import plan_solution
from quantum_calculator.application.validation.problem_validator import ProblemValidator
from quantum_calculator.domain.ports import (
    ConstantsEdition,
    EnvironmentProbe,
    Solver,
    UnitRegistry,
    Verifier,
)
from quantum_calculator.domain.problem_spec import ProblemSpec
from quantum_calculator.domain.run_record import RunRecord


@dataclass(frozen=True, slots=True)
class HomologatedMethod:
    solver: Solver
    verifier: Verifier


class SolveProblem:
    def __init__(
        self,
        validator: ProblemValidator,
        methods: Mapping[str, HomologatedMethod],
        constants: ConstantsEdition,
        units: UnitRegistry,
        environment: EnvironmentProbe,
    ) -> None:
        self._validator = validator
        self._methods = methods
        self._constants = constants
        self._units = units
        self._environment = environment

    def execute(self, spec: ProblemSpec) -> RunRecord:
        problem = self._validator.validate(spec)
        plan = plan_solution(problem)
        method = self._methods[plan.method.identifier]
        report = method.solver.solve(problem)
        verification = method.verifier.verify(problem, report)
        return RunRecord(
            problem=problem,
            plan=plan,
            report=report,
            verification=verification,
            constants=constants_in_use(problem, report, self._constants),
            constants_edition=self._constants.label,
            unit_registry_version=self._units.version,
            environment=self._environment.describe(),
        )
