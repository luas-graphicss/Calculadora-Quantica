from pathlib import Path

from benchmarks.harness.worker_task import solve_and_verify_measured
from quantum_calculator.application.numerical.validator import NumericalValidator
from quantum_calculator.application.solve_numerical import solve_and_verify_numerically
from quantum_calculator.catalog.numerical_catalog import HOMOLOGATED_NUMERICAL_CARDS
from quantum_calculator.domain.numerical.spec import NumericalSpec
from quantum_calculator.interfaces.serialization.decoding.input_decoder import decode_input
from quantum_calculator.method_registry import numerical_methods

CARDS = frozenset(card.identifier for card in HOMOLOGATED_NUMERICAL_CARDS)


def test_measured_task_returns_what_the_homologated_task_returns(
    numerical_cases: Path, numerical_validator: NumericalValidator
) -> None:
    spec = decode_input((numerical_cases / "electron_box_1nm_discrete.json").read_bytes(), CARDS)
    assert isinstance(spec, NumericalSpec)
    problem = numerical_validator.validate(spec)
    method = numerical_methods()[problem.context.card.method.identifier]

    measured = solve_and_verify_measured(method, problem)

    assert measured.outcome == solve_and_verify_numerically(method, problem)
    assert measured.solver_seconds > 0
    assert measured.verification_seconds > 0
    assert measured.peak_rss_bytes > 0
