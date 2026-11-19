from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from quantum_calculator.application.statements.budget import DEFAULT_WALL_SECONDS
from quantum_calculator.application.workbench.csv_tables import CSV_MEDIA_TYPE, table_csv
from quantum_calculator.application.workbench.submit_run import Submission
from quantum_calculator.interfaces.api.bodies import read_capped
from quantum_calculator.interfaces.api.encoding.answers import encode_answers
from quantum_calculator.interfaces.api.encoding.comparisons import encode_comparison
from quantum_calculator.interfaces.api.encoding.runs import (
    encode_run_details,
    encode_run_document,
    encode_run_list,
)
from quantum_calculator.interfaces.api.parameters import (
    ComparedRun,
    DisplayUnit,
    IdempotencyKey,
    ParentRun,
    RunIdentifier,
    TableName,
    TimeLimit,
)
from quantum_calculator.interfaces.serialization.decoding.json_document import MAX_DOCUMENT_BYTES
from quantum_calculator.workbench_composition import Workbench

_OK = 200
_ACCEPTED = 202


def runs_router(workbench: Workbench) -> APIRouter:
    router = APIRouter(tags=["runs"])

    @router.post("/runs")
    async def submit(
        request: Request,
        idempotency_key: IdempotencyKey,
        parent: ParentRun = None,
        time_limit: TimeLimit = DEFAULT_WALL_SECONDS,
    ) -> JSONResponse:
        source = await read_capped(request, MAX_DOCUMENT_BYTES)
        receipt = await run_in_threadpool(
            workbench.submit.execute, Submission(source, idempotency_key, time_limit, parent)
        )
        return JSONResponse(
            encode_run_document(receipt.run), status_code=_ACCEPTED if receipt.created else _OK
        )

    @router.get("/runs")
    def list_runs() -> JSONResponse:
        return JSONResponse(encode_run_list(workbench.history.recent()))

    @router.get("/runs/{identifier}")
    def read_run(identifier: RunIdentifier) -> JSONResponse:
        details = workbench.history.details(identifier)
        display = workbench.display.execute(identifier, None)
        return JSONResponse(encode_run_details(details, display.alternatives))

    @router.post("/runs/{identifier}/cancellation")
    def cancel(identifier: RunIdentifier) -> JSONResponse:
        return JSONResponse(encode_run_document(workbench.cancel.execute(identifier)))

    @router.get("/runs/{identifier}/answers")
    def read_answers(identifier: RunIdentifier, unit: DisplayUnit = None) -> JSONResponse:
        return JSONResponse(encode_answers(identifier, workbench.display.execute(identifier, unit)))

    @router.get("/runs/{identifier}/tables/{name}")
    def read_table(identifier: RunIdentifier, name: TableName) -> JSONResponse:
        return JSONResponse(workbench.history.table(identifier, name))

    @router.get("/runs/{identifier}/tables/{name}/csv")
    def download_table(identifier: RunIdentifier, name: TableName) -> Response:
        table = workbench.history.table(identifier, name)
        return _download(table_csv(table), CSV_MEDIA_TYPE, f"{name}.csv")

    @router.get("/runs/{identifier}/package")
    def export_package(identifier: RunIdentifier) -> Response:
        package = workbench.export_package.execute(identifier)
        return _download(package.content, "application/zip", package.file_name)

    @router.get("/comparisons")
    def compare(base: ComparedRun, other: ComparedRun) -> JSONResponse:
        return JSONResponse(encode_comparison(workbench.compare.execute(base, other)))

    return router


def _download(content: bytes, media_type: str, file_name: str) -> Response:
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
