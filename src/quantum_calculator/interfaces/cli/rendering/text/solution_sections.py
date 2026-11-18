from quantum_calculator.domain.statement_cards import StatementField
from quantum_calculator.domain.symbolic_solution import StatementRunRecord, SymbolicSolverReport
from quantum_calculator.domain.verification import VerificationReport, VerificationStatus
from quantum_calculator.interfaces.cli.rendering.text.formatting import section
from quantum_calculator.notation.rendering.conditions import render_condition
from quantum_calculator.notation.rendering.text import render_text

_VERDICTS = {
    VerificationStatus.PASSED: "Candidata aprovada",
    VerificationStatus.CONDITIONAL: "Candidata aprovada sob condição",
    VerificationStatus.INCONCLUSIVE: "Revisão inconclusiva da candidata",
    VerificationStatus.FAILED: "Candidata reprovada",
}
_ANSWER_DOMAIN = ("Validade", "vale")
_CANDIDATE_DOMAIN = ("Domínio da candidata", "está definida")


def solution_answer_lines(record: StatementRunRecord, unit: str) -> list[str]:
    answer = render_text(record.report.answer)
    verification = _verification_summary(record.verification)
    if _is_review(record):
        return [
            f"{_VERDICTS[record.verification.status]}: {answer}",
            f"revisão por substituição; {unit}; {verification}",
        ]
    return [answer, f"resultado {record.report.nature.value}; {unit}; {verification}"]


def solution_sections(record: StatementRunRecord) -> list[str]:
    report = record.report
    title, holds = _CANDIDATE_DOMAIN if _is_review(record) else _ANSWER_DOMAIN
    lines = section(title, _domain(report, holds))
    if report.assumptions:
        lines += section(
            "Hipóteses que o domínio declarado não confirma",
            [render_condition(condition) for condition in report.assumptions],
        )
    if report.special_cases:
        lines += section(
            "Casos especiais",
            [
                f"se {render_text(case.when)}: {render_text(case.answer)}"
                for case in report.special_cases
            ],
        )
    if report.arbitrary_constants:
        lines += section("Constantes arbitrárias", [", ".join(report.arbitrary_constants)])
    return [*lines, *section("Memória de cálculo", _calculation(record))]


def _verification_summary(report: VerificationReport) -> str:
    failed = [
        check.identifier for check in report.checks if check.status is VerificationStatus.FAILED
    ]
    reasons = f" ({', '.join(failed)})" if failed else ""
    return f"verificação: {report.status.value}{reasons}"


def _is_review(record: StatementRunRecord) -> bool:
    return StatementField.CANDIDATE in record.problem.card.required_fields


def _domain(report: SymbolicSolverReport, holds: str) -> list[str]:
    if report.validity:
        return [f"{holds} onde {render_condition(condition)}" for condition in report.validity]
    if report.assumptions:
        return ["nenhuma exclusão nas variáveis; depende das hipóteses listadas a seguir"]
    return [f"sem exclusões: {holds} em todo o domínio declarado"]


def _calculation(record: StatementRunRecord) -> list[str]:
    method = record.plan.method
    steps = [
        f"{index}. {step.description}: {render_text(step.expression)}"
        for index, step in enumerate(record.report.steps, start=1)
    ]
    return [f"método: {method.identifier} ({method.nature.value})", method.justification, *steps]
