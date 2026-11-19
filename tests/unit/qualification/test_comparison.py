import pytest

from qualification.comparison import (
    deviation_from,
    differences_from_homologation,
    disagreements_with_oracle,
)
from qualification.documents import Expectation, ExpectedValue, Observation, Refusal

_REFUSAL = Refusal(category="invalid_input", code="dimension_mismatch", pointer="/parameters/width")


def _expectation(
    *,
    values: list[ExpectedValue] | None = None,
    verification: str | None = "passed",
    exit_code: int = 0,
    refusal: Refusal | None = None,
    texts: dict[str, str] | None = None,
) -> Expectation:
    return Expectation(
        identifier="numerical/decay_trajectory",
        family="numerical",
        card="ode.initial_value.explicit_runge_kutta",
        input="reference_cases/numerical/decay_trajectory.json",
        command="solve",
        oracle="y(t) = exp(-k t)",
        exit_code=exit_code,
        verification=verification,
        not_passed=[],
        values=values or [],
        texts=texts or {},
        refusal=refusal,
    )


def _observation(
    *,
    values: dict[str, float] | None = None,
    verification: str | None = "passed",
    exit_code: int = 0,
    card: str | None = "ode.initial_value.explicit_runge_kutta",
    refusals: list[Refusal] | None = None,
    texts: dict[str, str] | None = None,
    not_passed: list[str] | None = None,
) -> Observation:
    return Observation(
        exit_code=exit_code,
        card=card,
        verification=verification,
        not_passed=not_passed or [],
        values=values or {},
        texts=texts or {},
        refusals=refusals or [],
    )


def _final_y(tolerance: float, comparison: str = "absolute") -> ExpectedValue:
    assert comparison in ("absolute", "relative")
    return ExpectedValue(
        name="final_y",
        expected=0.5,
        tolerance=tolerance,
        comparison="relative" if comparison == "relative" else "absolute",
    )


def test_an_answer_inside_the_tolerance_agrees_with_the_oracle() -> None:
    expectation = _expectation(values=[_final_y(1e-6)])

    assert disagreements_with_oracle(expectation, _observation(values={"final_y": 0.5000005})) == []


def test_an_answer_outside_the_tolerance_names_the_deviation_and_the_limit() -> None:
    expectation = _expectation(values=[_final_y(1e-6)])

    found = disagreements_with_oracle(expectation, _observation(values={"final_y": 0.50001}))

    assert len(found) == 1
    assert "final_y = 0.50001 deviates" in found[0]
    assert "above 1.000e-06" in found[0]


def test_a_relative_tolerance_is_measured_against_the_expected_value() -> None:
    assert deviation_from(_final_y(1e-3, "relative"), 0.505) == pytest.approx(0.01)
    assert deviation_from(_final_y(1e-3), 0.505) == pytest.approx(0.005)


def test_a_missing_answer_and_a_value_that_is_not_a_number_never_agree() -> None:
    expectation = _expectation(values=[_final_y(1e-6)])

    missing = disagreements_with_oracle(expectation, _observation())
    undefined = disagreements_with_oracle(
        expectation, _observation(values={"final_y": float("nan")})
    )

    assert missing == ["final_y is missing from the answers"]
    assert len(undefined) == 1


def test_a_verdict_that_changed_is_reported_even_when_the_values_agree() -> None:
    expectation = _expectation(values=[_final_y(1e-6)])
    observed = _observation(
        values={"final_y": 0.5},
        verification="inconclusive",
        exit_code=5,
        not_passed=["mesh_refinement"],
    )

    assert disagreements_with_oracle(expectation, observed) == [
        "exit code 5, expected 0",
        "verification 'inconclusive', expected 'passed'",
        "checks not passed ['mesh_refinement'], expected []",
    ]


def test_a_refusal_must_carry_the_labelled_diagnostic() -> None:
    expectation = _expectation(verification=None, exit_code=3, refusal=_REFUSAL)
    elsewhere = Refusal(category="invalid_input", code="dimension_mismatch", pointer="/requested")

    labelled = _observation(verification=None, exit_code=3, card=None, refusals=[_REFUSAL])
    moved = _observation(verification=None, exit_code=3, card=None, refusals=[elsewhere])

    assert disagreements_with_oracle(expectation, labelled) == []
    assert len(disagreements_with_oracle(expectation, moved)) == 1


def test_an_answered_case_must_come_from_the_labelled_card() -> None:
    found = disagreements_with_oracle(_expectation(), _observation(card="another.card"))

    assert found == ["card 'another.card', expected 'ode.initial_value.explicit_runge_kutta'"]


def test_another_installation_may_differ_inside_the_tolerance_only() -> None:
    expectation = _expectation(values=[_final_y(1e-6)])
    homologated = _observation(values={"final_y": 0.5000001})

    inside = differences_from_homologation(
        expectation, homologated, _observation(values={"final_y": 0.4999999})
    )
    outside = differences_from_homologation(
        expectation, homologated, _observation(values={"final_y": 0.6})
    )

    assert inside == []
    assert len(outside) == 1


def test_another_installation_must_read_the_same_text_as_the_homologation() -> None:
    expectation = _expectation(texts={"structure": "(symbol x)"})
    homologated = _observation(texts={"structure": "(symbol x)"})

    found = differences_from_homologation(
        expectation, homologated, _observation(texts={"structure": "(symbol y)"})
    )

    assert found == ["texts {'structure': '(symbol y)'}, homologated {'structure': '(symbol x)'}"]
