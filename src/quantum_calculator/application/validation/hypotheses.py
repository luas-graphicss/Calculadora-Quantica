from quantum_calculator.domain.cards import HypothesisRule
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    json_pointer,
    quote_user_text,
)
from quantum_calculator.domain.problem_spec import HypothesisInput
from quantum_calculator.domain.validated_problem import ConfirmedHypothesis


def confirm_hypotheses(
    rules: tuple[HypothesisRule, ...],
    given: tuple[HypothesisInput, ...],
    diagnostics: list[Diagnostic],
) -> tuple[ConfirmedHypothesis, ...]:
    declared = {hypothesis.key: hypothesis.value for hypothesis in given}
    confirmed: list[ConfirmedHypothesis] = []
    for rule in rules:
        pointer = json_pointer("hypotheses", rule.key)
        expected = f'"{rule.required_value}"'
        value = declared.pop(rule.key, None)
        if value is None:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.HYPOTHESIS_NOT_CONFIRMED,
                    pointer,
                    f"A hipótese {rule.key} não foi confirmada. {rule.statement}",
                    expected,
                )
            )
        elif value != rule.required_value:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.UNSUPPORTED_HYPOTHESIS,
                    pointer,
                    f"A ficha só cobre {rule.key} = {expected}; "
                    f"a entrada declara {quote_user_text(value)}.",
                    expected,
                )
            )
        else:
            confirmed.append(ConfirmedHypothesis(rule.key, value, rule.statement))
    known = ", ".join(rule.key for rule in rules)
    diagnostics.extend(
        Diagnostic(
            DiagnosticCode.UNEXPECTED_FIELD,
            json_pointer("hypotheses", key),
            f"A ficha não define a hipótese {quote_user_text(key)}.",
            f"uma destas hipóteses: {known}",
        )
        for key in declared
    )
    return tuple(confirmed)
