from urllib.parse import parse_qs

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from quantum_calculator.interfaces.api.bodies import read_capped
from quantum_calculator.interfaces.api.documents import API_PREFIX
from quantum_calculator.interfaces.api.errors import ApiError
from quantum_calculator.interfaces.api.security.session import SESSION_COOKIE, SessionGate

_MAX_FORM_BYTES = 1024
_SEE_OTHER = 303
_NO_CONTENT = 204
_UNAUTHORIZED = 401
_FORBIDDEN = 403
_INTERFACE = "/"


def session_router(gate: SessionGate) -> APIRouter:
    router = APIRouter(tags=["session"])

    @router.post("/session", status_code=_SEE_OTHER)
    async def open_session(request: Request) -> Response:
        form = parse_qs((await read_capped(request, _MAX_FORM_BYTES)).decode("utf-8", "replace"))
        session = gate.admit("".join(form.get("code", [])))
        if session is None:
            raise ApiError(
                _FORBIDDEN,
                "launch_code_refused",
                "O código de acesso não é o desta execução da calculadora. Abra de novo o "
                "arquivo de acesso indicado no terminal.",
            )
        response = RedirectResponse(_INTERFACE, status_code=_SEE_OTHER)
        response.set_cookie(
            SESSION_COOKIE, session, httponly=True, samesite="strict", path=API_PREFIX
        )
        return response

    @router.get("/session", status_code=_NO_CONTENT)
    def confirm_session(request: Request) -> Response:
        recognized = gate.recognizes(request.cookies.get(SESSION_COOKIE))
        return Response(status_code=_NO_CONTENT if recognized else _UNAUTHORIZED)

    return router
