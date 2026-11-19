import math
from dataclasses import dataclass

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode
from quantum_calculator.domain.execution import BudgetResource, ExecutionBudget

DEFAULT_WALL_SECONDS = 30.0
MAX_WALL_SECONDS = 600.0

_MEBIBYTE = 1024**2
_MEMORY_BYTES = 2048 * _MEBIBYTE
_DISCARDED = "O processo foi encerrado e nenhum resultado parcial foi aproveitado."


@dataclass(frozen=True, slots=True)
class BudgetWording:
    calculation: str
    expansion: str
    remedy: str


SYMBOLIC_WORDING = BudgetWording(
    calculation="O cálculo simbólico",
    expansion="A expansão simbólica",
    remedy="um enunciado mais simples ou um limite maior; o próximo cálculo não é afetado",
)
NUMERICAL_WORDING = BudgetWording(
    calculation="O cálculo numérico",
    expansion="O cálculo numérico",
    remedy="uma resolução menor ou um limite maior; o próximo cálculo não é afetado",
)


def symbolic_budget(wall_seconds: float = DEFAULT_WALL_SECONDS) -> ExecutionBudget:
    return ExecutionBudget(
        wall_seconds=wall_seconds,
        cpu_seconds=math.ceil(wall_seconds),
        memory_bytes=_MEMORY_BYTES,
    )


DEFAULT_SYMBOLIC_BUDGET = symbolic_budget()


def describe_budget(budget: ExecutionBudget) -> str:
    return (
        f"{budget.wall_seconds:g} s de relógio, {budget.cpu_seconds} s de CPU e "
        f"{budget.memory_bytes // _MEBIBYTE} MiB de memória"
    )


def budget_diagnostic(
    resource: BudgetResource, budget: ExecutionBudget, wording: BudgetWording = SYMBOLIC_WORDING
) -> Diagnostic:
    if resource is BudgetResource.MEMORY:
        return Diagnostic(
            DiagnosticCode.MEMORY_BUDGET_EXCEEDED,
            "",
            f"{wording.calculation} passou do limite de {budget.memory_bytes // _MEBIBYTE} MiB "
            f"de memória. {_DISCARDED}",
            wording.remedy,
        )
    if resource is BudgetResource.RECURSION_DEPTH:
        return Diagnostic(
            DiagnosticCode.EXPRESSION_TOO_DEEP,
            "",
            f"{wording.expansion} passou da profundidade suportada. {_DISCARDED}",
            wording.remedy,
        )
    spent = (
        f"{budget.cpu_seconds} s de CPU"
        if resource is BudgetResource.CPU_TIME
        else f"{budget.wall_seconds:g} s de relógio"
    )
    return Diagnostic(
        DiagnosticCode.TIME_BUDGET_EXCEEDED,
        "",
        f"{wording.calculation} passou do limite de {spent}. {_DISCARDED}",
        wording.remedy,
    )
