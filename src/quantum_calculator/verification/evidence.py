import sympy

from quantum_calculator.algebra.builder import ExpressionBuilder
from quantum_calculator.algebra.conditions import UndefinedExpressionError, analyze_domain
from quantum_calculator.algebra.identity import SAMPLE_COUNT, IdentityOutcome, IdentityVerdict
from quantum_calculator.algebra.reader import UnregisteredOperationError, read_expression
from quantum_calculator.domain.diagnostics import DiagnosticCode
from quantum_calculator.domain.expression_dimensions import DimensionAnalyzer, describe_dimension
from quantum_calculator.domain.expressions import Number, Statement
from quantum_calculator.domain.statement_errors import StatementError
from quantum_calculator.domain.statements import ValidatedStatement
from quantum_calculator.domain.symbolic_solution import SymbolicSolverReport
from quantum_calculator.domain.verification import (
    EvidenceKind,
    SkippedCheck,
    VerificationCheck,
    VerificationStatus,
)
from quantum_calculator.notation.rendering.conditions import render_condition, render_conditions
from quantum_calculator.notation.rendering.text import render_text

_DOMAIN_CHECK = "declared_domain_suffices"
_DOMAIN_STATEMENT = "A resposta vale para todos os valores dos parâmetros no domínio declarado."
_DIMENSION_CHECK = "dimensional_consistency"
_DIMENSION_STATEMENT = "A resposta tem a dimensão que o enunciado e as unidades declaradas exigem."


def identity_check(identifier: str, statement: str, verdict: IdentityVerdict) -> VerificationCheck:
    residual = describe(verdict.residual)
    if verdict.outcome is IdentityOutcome.PROVEN:
        return VerificationCheck(
            identifier,
            EvidenceKind.PROOF,
            VerificationStatus.PASSED,
            statement,
            "o resíduo se reduz a zero por simplificação simbólica",
        )
    if verdict.outcome is IdentityOutcome.UNDECIDED:
        return VerificationCheck(
            identifier,
            EvidenceKind.NUMERICAL_EVIDENCE,
            VerificationStatus.INCONCLUSIVE,
            statement,
            f"a simplificação não reduziu o resíduo {residual} a zero; ele se anula nos "
            f"{SAMPLE_COUNT} pontos amostrados, mas amostragem não prova a identidade",
        )
    if verdict.outcome is IdentityOutcome.REFUTED_NUMERICALLY:
        return VerificationCheck(
            identifier,
            EvidenceKind.NUMERICAL_EVIDENCE,
            VerificationStatus.FAILED,
            statement,
            f"em {verdict.witness} o resíduo vale aproximadamente {verdict.value_at_witness}; "
            "a avaliação numérica indica que a identidade não vale",
        )
    observed = (
        f"o resíduo {residual} não se anula em nenhum ponto do domínio declarado"
        if verdict.witness is None
        else f"em {verdict.witness} o resíduo vale {verdict.value_at_witness}, diferente de zero"
    )
    return VerificationCheck(
        identifier, EvidenceKind.PROOF, VerificationStatus.FAILED, statement, observed
    )


def declared_domain_check(
    problem: ValidatedStatement, builder: ExpressionBuilder, *statements: Statement
) -> VerificationCheck:
    try:
        analysis = analyze_domain(builder, problem.variable_names, *statements)
    except UndefinedExpressionError as error:
        return _domain_check(
            VerificationStatus.FAILED,
            f"a resposta exige {render_condition(error.condition)}, que nunca vale no domínio "
            "declarado",
        )
    if analysis.assumptions:
        return _domain_check(
            VerificationStatus.CONDITIONAL,
            f"vale somente com {render_conditions(analysis.assumptions)}, hipótese que o "
            "domínio declarado dos parâmetros não confirma",
        )
    return _domain_check(
        VerificationStatus.PASSED, "nenhuma hipótese além do domínio declarado é necessária"
    )


def dimension_check(
    problem: ValidatedStatement, report: SymbolicSolverReport
) -> VerificationCheck | SkippedCheck:
    if report.arbitrary_constants:
        return SkippedCheck(
            _DIMENSION_CHECK,
            "A resposta tem uma constante arbitrária, cuja dimensão é fixada pelo contexto.",
        )
    value = report.answer.right
    expected = problem.result_dimension
    analyzer = DimensionAnalyzer({symbol.name: symbol for symbol in problem.symbols})
    try:
        found = analyzer.check(value)
    except StatementError as error:
        if error.code is DiagnosticCode.DIMENSION_MISMATCH:
            return _dimension_check(VerificationStatus.FAILED, error.message)
        return SkippedCheck(
            _DIMENSION_CHECK,
            "A forma simplificada usa uma potência ou raiz de grandeza com dimensão que a "
            "análise dimensional não classifica.",
        )
    is_consistent = found == expected or (isinstance(value, Number) and value.value == 0)
    return _dimension_check(
        VerificationStatus.PASSED if is_consistent else VerificationStatus.FAILED,
        f"resposta com dimensão {describe_dimension(found)}; o enunciado exige "
        f"{describe_dimension(expected)}",
    )


def describe(value: sympy.Expr) -> str:
    try:
        return render_text(read_expression(value))
    except UnregisteredOperationError:
        return str(sympy.sstr(value))


def _domain_check(status: VerificationStatus, observed: str) -> VerificationCheck:
    return VerificationCheck(_DOMAIN_CHECK, EvidenceKind.PROOF, status, _DOMAIN_STATEMENT, observed)


def _dimension_check(status: VerificationStatus, observed: str) -> VerificationCheck:
    return VerificationCheck(
        _DIMENSION_CHECK, EvidenceKind.CONSISTENCY_TEST, status, _DIMENSION_STATEMENT, observed
    )
