import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.conditions import (
    DomainAnalysis,
    UndefinedExpressionError,
    analyze_domain,
)
from quantum_calculator.algebra.reader import UnregisteredOperationError, read_expression
from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, ProblemRejectedError
from quantum_calculator.domain.expressions import Expression, Statement
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import DomainCondition
from quantum_calculator.notation.rendering.conditions import render_condition

STATEMENT_POINTER = "/statement"

_COVERED_EXPRESSION = "um enunciado dentro da cobertura declarada na ficha"
_FIXED_PARAMETER_CASE = (
    'um domínio declarado que fixe o caso do parâmetro, como "positive", "negative" ou "nonzero"'
)
_CASE_SPLIT = "Piecewise"
_CONSTANT = "C"


def rejection(code: DiagnosticCode, message: str, expected: str) -> ProblemRejectedError:
    return ProblemRejectedError((Diagnostic(code, STATEMENT_POINTER, message, expected),))


def outside_coverage(message: str, expected: str = _COVERED_EXPRESSION) -> ProblemRejectedError:
    return rejection(DiagnosticCode.OUTSIDE_COVERAGE, message, expected)


def undefined_expression(condition: DomainCondition) -> ProblemRejectedError:
    return rejection(
        DiagnosticCode.UNDEFINED_EXPRESSION,
        "A expressão não está definida em nenhum ponto do domínio declarado: ela exige "
        f"{render_condition(condition)}.",
        "uma expressão definida em algum ponto do domínio declarado",
    )


def read_result(value: sympy.Expr) -> Expression:
    try:
        return read_expression(value)
    except UnregisteredOperationError as error:
        if error.operation == _CASE_SPLIT:
            raise outside_coverage(
                "O resultado muda de forma conforme o valor de um parâmetro, e o domínio "
                "declarado não fixa o caso.",
                _FIXED_PARAMETER_CASE,
            ) from error
        raise outside_coverage(
            f"O resultado pede a operação {error.operation}, que não está entre as registradas."
        ) from error


def solution_domain(
    problem: ValidatedStatement, builder: ExpressionBuilder, *statements: Statement
) -> DomainAnalysis:
    try:
        return analyze_domain(builder, problem.variable_names, *statements)
    except UndefinedExpressionError as error:
        raise undefined_expression(error.condition) from error


def fresh_constant(problem: ValidatedStatement) -> str:
    declared = {symbol.name for symbol in problem.symbols}
    if _CONSTANT not in declared:
        return _CONSTANT
    index = 1
    while f"{_CONSTANT}_{index}" in declared:
        index += 1
    return f"{_CONSTANT}_{index}"
