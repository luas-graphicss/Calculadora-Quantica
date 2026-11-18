from dataclasses import dataclass

import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.application.statements.statement_validator import StatementValidator
from quantum_calculator.domain.diagnostics import Diagnostic, ProblemRejectedError
from quantum_calculator.domain.dimensions import DIMENSIONLESS
from quantum_calculator.domain.expressions import Equation, Expression
from quantum_calculator.domain.ports import StatementSolver, StatementVerifier
from quantum_calculator.domain.statements import (
    BoundSymbol,
    Notation,
    SymbolDomain,
    SymbolRole,
    ValidatedStatement,
)
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport
from quantum_calculator.domain.verification import (
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)
from quantum_calculator.notation.rendering.conditions import render_condition
from quantum_calculator.notation.rendering.text import render_text
from support.notation import read, read_expression_text
from support.statements import SymbolDeclarations, statement_spec


@dataclass(frozen=True, slots=True)
class SymbolicResult:
    problem: ValidatedStatement
    report: SymbolicSolverReport
    verification: VerificationReport

    @property
    def value(self) -> Expression:
        return self.report.answer.right

    @property
    def answer(self) -> str:
        return render_text(self.report.answer)

    @property
    def validity(self) -> list[str]:
        return [render_condition(condition) for condition in self.report.validity]

    @property
    def assumptions(self) -> list[str]:
        return [render_condition(condition) for condition in self.report.assumptions]

    @property
    def statuses(self) -> dict[str, VerificationStatus]:
        return {check.identifier: check.status for check in self.verification.checks}

    def check(self, identifier: str) -> VerificationCheck:
        return next(item for item in self.verification.checks if item.identifier == identifier)

    def equals(self, expected: str) -> bool:
        return same_function(self.problem, self.report.arbitrary_constants, self.value, expected)

    def is_valid_when(self, expected: str) -> bool:
        return expected in self.validity


class SymbolicBench:
    def __init__(
        self, validator: StatementValidator, solver: StatementSolver, verifier: StatementVerifier
    ) -> None:
        self._validator = validator
        self._solver = solver
        self._verifier = verifier

    def run(
        self,
        statement: str,
        symbols: SymbolDeclarations,
        notation: str = "text",
        /,
        **fields: object,
    ) -> SymbolicResult:
        problem = self._validator.validate(statement_spec(statement, symbols, notation, **fields))
        report = self._solver.solve(problem)
        return SymbolicResult(problem, report, self._verifier.verify(problem, report))

    def refusal(
        self,
        statement: str,
        symbols: SymbolDeclarations,
        notation: str = "text",
        /,
        **fields: object,
    ) -> Diagnostic:
        try:
            self.run(statement, symbols, notation, **fields)
        except ProblemRejectedError as rejection:
            (diagnostic,) = rejection.diagnostics
            return diagnostic
        raise AssertionError(f"{statement!r} was solved")

    def verify(self, result: SymbolicResult, report: SymbolicSolverReport) -> SymbolicResult:
        return SymbolicResult(result.problem, report, self._verifier.verify(result.problem, report))


def parsed(
    problem: ValidatedStatement, report: SymbolicSolverReport, expression: str
) -> Expression:
    return read_expression_text(expression, _symbol_table(problem, report.arbitrary_constants))


def answer_value(
    problem: ValidatedStatement, constants: tuple[str, ...], answer: str
) -> Expression:
    equation = read(Notation.TEXT, answer, _symbol_table(problem, constants))
    if not isinstance(equation, Equation):
        raise TypeError(f"{answer!r} is not an equation")
    return equation.right


def same_function(
    problem: ValidatedStatement, constants: tuple[str, ...], value: Expression, expected: str
) -> bool:
    builder = ExpressionBuilder(problem.symbols, constants)
    claimed = read_expression_text(expected, _symbol_table(problem, constants))
    return bool(sympy.simplify(builder.build(value) - builder.build(claimed)) == 0)


def _symbol_table(
    problem: ValidatedStatement, constants: tuple[str, ...]
) -> dict[str, BoundSymbol]:
    table = {symbol.name: symbol for symbol in problem.symbols}
    for constant in constants:
        table[constant] = BoundSymbol(
            constant, SymbolRole.PARAMETER, SymbolDomain.REAL, DIMENSIONLESS, "1", None
        )
    return table
