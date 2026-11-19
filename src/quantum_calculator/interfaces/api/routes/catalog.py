from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from quantum_calculator.application.statements.budget import DEFAULT_WALL_SECONDS
from quantum_calculator.application.workbench.summaries import REJECTION, document_kind
from quantum_calculator.interfaces.api.bodies import read_capped
from quantum_calculator.interfaces.api.encoding.catalog import encode_workbench_catalog
from quantum_calculator.interfaces.api.parameters import TimeLimit
from quantum_calculator.interfaces.serialization.decoding.json_document import MAX_DOCUMENT_BYTES
from quantum_calculator.workbench_composition import Workbench

_OK = 200
_UNPROCESSABLE = 422


def catalog_router(workbench: Workbench) -> APIRouter:
    router = APIRouter(tags=["catalog"])
    catalog = encode_workbench_catalog(workbench.catalog)

    @router.get("/catalog")
    def read_catalog() -> JSONResponse:
        return JSONResponse(catalog)

    @router.post("/validations")
    async def validate(
        request: Request, time_limit: TimeLimit = DEFAULT_WALL_SECONDS
    ) -> JSONResponse:
        source = await read_capped(request, MAX_DOCUMENT_BYTES)
        interpretation = await run_in_threadpool(workbench.documents.interpret, source, time_limit)
        refused = document_kind(interpretation) == REJECTION
        return JSONResponse(interpretation, status_code=_UNPROCESSABLE if refused else _OK)

    return router
