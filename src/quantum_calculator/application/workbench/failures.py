from quantum_calculator.application.workbench.summaries import CALCULATION_FAILURE
from quantum_calculator.domain.workbench.documents import Document

FAILURE_SCHEMA_VERSION = "1.0"
CALCULATION_FAILED = "calculation_failed"
INTERNAL_ERROR = "internal_error"

_NOTHING_KEPT = "nenhum resultado parcial foi aproveitado"


def process_failure(exit_code: int | None) -> Document:
    return _failure(
        CALCULATION_FAILED,
        "O processo de cálculo terminou sem devolver resultado (código de saída "
        f"{exit_code}); {_NOTHING_KEPT}.",
    )


def internal_failure() -> Document:
    return _failure(
        INTERNAL_ERROR,
        f"A calculadora encontrou um erro interno ao executar este cálculo; {_NOTHING_KEPT}. "
        "As execuções anteriores não foram afetadas.",
    )


def _failure(category: str, message: str) -> Document:
    return {
        "document": CALCULATION_FAILURE,
        "schema_version": FAILURE_SCHEMA_VERSION,
        "category": category,
        "message": message,
    }
