from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from quantum_calculator.application.workbench.display_answers import DisplayUnitRefusedError
from quantum_calculator.application.workbench.export_package import RunStillActiveError
from quantum_calculator.application.workbench.read_history import TableNotFoundError
from quantum_calculator.application.workbench.submit_run import (
    IdempotencyConflictError,
    SubmissionRejectedError,
)
from quantum_calculator.domain.workbench.artifacts import ArtifactIntegrityError
from quantum_calculator.domain.workbench.packages import PackageRejectedError
from quantum_calculator.domain.workbench.runs import RunNotFoundError
from quantum_calculator.interfaces.api.documents import error_document

_BAD_REQUEST = 400
_NOT_FOUND = 404
_CONFLICT = 409
_UNPROCESSABLE = 422
_INTERNAL_ERROR = 500


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def refusal(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(error_document(code, message), status_code=status)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    def api_error(_request: Request, error: ApiError) -> JSONResponse:
        return refusal(error.status, error.code, error.message)

    @app.exception_handler(SubmissionRejectedError)
    def submission_rejected(_request: Request, error: SubmissionRejectedError) -> JSONResponse:
        return JSONResponse(error.rejection, status_code=_UNPROCESSABLE)

    @app.exception_handler(RunNotFoundError)
    def run_not_found(_request: Request, error: RunNotFoundError) -> JSONResponse:
        return refusal(
            _NOT_FOUND, "run_not_found", f"A execução {error.identifier} não está no histórico."
        )

    @app.exception_handler(TableNotFoundError)
    def table_not_found(_request: Request, error: TableNotFoundError) -> JSONResponse:
        return refusal(
            _NOT_FOUND,
            "table_not_found",
            f"A execução {error.run_identifier} não tem a tabela {error.name}.",
        )

    @app.exception_handler(IdempotencyConflictError)
    def idempotency_conflict(_request: Request, error: IdempotencyConflictError) -> JSONResponse:
        return refusal(
            _CONFLICT,
            "idempotency_conflict",
            f"A chave de idempotência já pertence à execução {error.run_identifier}, enviada "
            "com outra entrada. Uma entrada alterada precisa de uma chave nova.",
        )

    @app.exception_handler(RunStillActiveError)
    def run_still_active(_request: Request, error: RunStillActiveError) -> JSONResponse:
        return refusal(
            _CONFLICT,
            "run_still_active",
            f"A execução {error.identifier} ainda não terminou: só uma execução encerrada é "
            "exportada.",
        )

    @app.exception_handler(DisplayUnitRefusedError)
    def display_unit_refused(_request: Request, error: DisplayUnitRefusedError) -> JSONResponse:
        accepted = ", ".join(error.alternatives) or "nenhuma"
        return refusal(
            _UNPROCESSABLE,
            "display_unit_refused",
            f"As respostas desta execução não podem ser exibidas em {error.unit!r}. Unidades "
            f"aceitas: {accepted}.",
        )

    @app.exception_handler(PackageRejectedError)
    def package_rejected(_request: Request, error: PackageRejectedError) -> JSONResponse:
        return refusal(_UNPROCESSABLE, "package_refused", error.reason)

    @app.exception_handler(ArtifactIntegrityError)
    def artifact_integrity(_request: Request, _error: ArtifactIntegrityError) -> JSONResponse:
        return refusal(
            _INTERNAL_ERROR,
            "artifact_integrity",
            "Um arquivo do histórico não confere com o hash registrado; o conteúdo não foi "
            "exibido. As outras execuções não foram afetadas.",
        )

    @app.exception_handler(RequestValidationError)
    def invalid_request(_request: Request, error: RequestValidationError) -> JSONResponse:
        fields = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
            for issue in error.errors()
        )
        return refusal(
            _BAD_REQUEST, "invalid_request", f"A requisição não segue o formato da API: {fields}."
        )

    @app.exception_handler(HTTPException)
    def http_refusal(_request: Request, error: HTTPException) -> JSONResponse:
        return refusal(error.status_code, f"http_{error.status_code}", str(error.detail))
