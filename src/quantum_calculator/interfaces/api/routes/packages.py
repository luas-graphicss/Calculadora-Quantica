from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from quantum_calculator.adapters.storage.zip_packages import MAX_PACKAGE_BYTES
from quantum_calculator.interfaces.api.bodies import read_capped
from quantum_calculator.interfaces.api.encoding.runs import encode_run_document
from quantum_calculator.workbench_composition import Workbench

_OK = 200
_CREATED = 201


def packages_router(workbench: Workbench) -> APIRouter:
    router = APIRouter(tags=["packages"])

    @router.post("/imports")
    async def import_package(request: Request) -> JSONResponse:
        content = await read_capped(request, MAX_PACKAGE_BYTES)
        receipt = await run_in_threadpool(workbench.import_package.execute, content)
        return JSONResponse(
            encode_run_document(receipt.run), status_code=_CREATED if receipt.created else _OK
        )

    return router
