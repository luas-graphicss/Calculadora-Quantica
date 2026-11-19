from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends, FastAPI

from quantum_calculator.interfaces.api.documents import API_PREFIX, API_VERSION
from quantum_calculator.interfaces.api.errors import register_error_handlers
from quantum_calculator.interfaces.api.routes.catalog import catalog_router
from quantum_calculator.interfaces.api.routes.packages import packages_router
from quantum_calculator.interfaces.api.routes.runs import runs_router
from quantum_calculator.interfaces.api.routes.session import session_router
from quantum_calculator.interfaces.api.security.loopback_guard import LoopbackGuard
from quantum_calculator.interfaces.api.security.response_headers import ResponseHeaders
from quantum_calculator.interfaces.api.security.session import SessionGate, session_requirement
from quantum_calculator.interfaces.api.web_interface import mount_interface
from quantum_calculator.workbench_composition import Workbench


@dataclass(frozen=True, slots=True)
class ApiSettings:
    port: int
    web_root: Path | None


def create_api(workbench: Workbench, gate: SessionGate, settings: ApiSettings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        workbench.recover.execute()
        yield
        workbench.shut_down()

    app = FastAPI(
        title="Calculadora Quântica: API local",
        version=API_VERSION,
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    behind_session = [Depends(session_requirement(gate))]
    app.include_router(session_router(gate), prefix=API_PREFIX)
    for router in (catalog_router(workbench), runs_router(workbench), packages_router(workbench)):
        app.include_router(router, prefix=API_PREFIX, dependencies=behind_session)
    register_error_handlers(app)
    app.add_middleware(LoopbackGuard, port=settings.port)
    app.add_middleware(ResponseHeaders)
    mount_interface(app, settings.web_root)
    return app
