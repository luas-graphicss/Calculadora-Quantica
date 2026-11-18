from quantum_calculator.domain.expressions import Statement
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.statements import BoundSymbol, ValidatedStatement
from quantum_calculator.domain.symbolic_solution import StatementPlan, SymbolicSolverReport
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject
from quantum_calculator.interfaces.serialization.encoding.notated import (
    encode_condition,
    encode_notated,
)


class StatementEncoder:
    def __init__(self, units: UnitRegistry) -> None:
        self._units = units

    def encode_problem(self, problem: ValidatedStatement) -> JsonObject:
        card = problem.card
        spec = problem.spec
        candidate = None
        if problem.candidate is not None and spec.candidate is not None:
            candidate = _encode_read(spec.candidate, problem.candidate)
        return {
            "card": {
                "identifier": card.identifier,
                "version": card.version,
                "area": card.area,
                "problem_type": card.problem_type,
                "title": card.title,
                "selection": problem.selection.value,
            },
            "domain": list(card.domain),
            "notation": problem.notation.value,
            "statement": _encode_read(spec.statement, problem.statement),
            "symbols": [_encode_symbol(symbol) for symbol in problem.symbols],
            "conditions": [
                _encode_read(source, condition)
                for source, condition in zip(spec.conditions, problem.conditions, strict=True)
            ],
            "candidate": candidate,
            "result_unit": self._units.coherent_symbol(problem.result_dimension),
        }

    def encode_result(
        self, problem: ValidatedStatement, report: SymbolicSolverReport
    ) -> JsonObject:
        certificate = report.certificate
        return {
            "nature": report.nature.value,
            "answer": encode_notated(report.answer),
            "unit": self._units.coherent_symbol(problem.result_dimension),
            "validity": [encode_condition(condition) for condition in report.validity],
            "assumptions": [encode_condition(condition) for condition in report.assumptions],
            "special_cases": [
                {"when": encode_notated(case.when), "answer": encode_notated(case.answer)}
                for case in report.special_cases
            ],
            "arbitrary_constants": list(report.arbitrary_constants),
            "certificate": None if certificate is None else encode_notated(certificate),
            "steps": [
                {"description": step.description, "expression": encode_notated(step.expression)}
                for step in report.steps
            ],
        }


def encode_statement_plan(plan: StatementPlan) -> JsonObject:
    return {
        "method": plan.method.identifier,
        "nature": plan.method.nature.value,
        "justification": plan.method.justification,
        "budget": {
            "wall_seconds": plan.budget.wall_seconds,
            "cpu_seconds": plan.budget.cpu_seconds,
            "memory_bytes": plan.budget.memory_bytes,
        },
    }


def _encode_read(source: str, statement: Statement) -> JsonObject:
    return {"source": source, **encode_notated(statement)}


def _encode_symbol(symbol: BoundSymbol) -> JsonObject:
    return {
        "name": symbol.name,
        "role": symbol.role.value,
        "domain": symbol.domain.value,
        "unit": symbol.unit,
        "argument": symbol.argument,
    }
