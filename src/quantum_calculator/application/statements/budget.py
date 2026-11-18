import math

from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode
from quantum_calculator.domain.execution import BudgetResource, ExecutionBudget

DEFAULT_WALL_SECONDS = 30.0
MAX_WALL_SECONDS = 600.0

_MEBIBYTE = 1024**2
_MEMORY_BYTES = 2048 * _MEBIBYTE
_NEXT_CALCULATION = "um enunciado mais simples ou um limite maior; o próximo cálculo não é afetado"
_DISCARDED = "O processo foi encerrado e nenhum resultado parcial foi aproveitado."


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


def budget_diagnostic(resource: BudgetResource, budget: ExecutionBudget) -> Diagnostic:
    if resource is BudgetResource.MEMORY:
        return Diagnostic(
            DiagnosticCode.MEMORY_BUDGET_EXCEEDED,
            "",
            f"O cálculo simbólico passou do limite de {budget.memory_bytes // _MEBIBYTE} MiB de "
            f"memória. {_DISCARDED}",
            _NEXT_CALCULATION,
        )
    if resource is BudgetResource.RECURSION_DEPTH:
        return Diagnostic(
            DiagnosticCode.EXPRESSION_TOO_DEEP,
            "",
            f"A expansão simbólica passou da profundidade suportada. {_DISCARDED}",
            _NEXT_CALCULATION,
        )
    spent = (
        f"{budget.cpu_seconds} s de CPU"
        if resource is BudgetResource.CPU_TIME
        else f"{budget.wall_seconds:g} s de relógio"
    )
    return Diagnostic(
        DiagnosticCode.TIME_BUDGET_EXCEEDED,
        "",
        f"O cálculo simbólico passou do limite de {spent}. {_DISCARDED}",
        _NEXT_CALCULATION,
    )
