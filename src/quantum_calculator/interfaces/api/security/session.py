import hmac
import secrets
from collections.abc import Callable

from fastapi import Request

from quantum_calculator.interfaces.api.errors import ApiError

SESSION_COOKIE = "qcalc_session"

_SECRET_BYTES = 32
_UNAUTHORIZED = 401


class SessionGate:
    def __init__(self) -> None:
        self._launch_code = secrets.token_urlsafe(_SECRET_BYTES)
        self._session_secret = secrets.token_urlsafe(_SECRET_BYTES)

    @property
    def launch_code(self) -> str:
        return self._launch_code

    def admit(self, presented_code: str) -> str | None:
        if _matches(presented_code, self._launch_code):
            return self._session_secret
        return None

    def recognizes(self, presented_session: str | None) -> bool:
        return presented_session is not None and _matches(presented_session, self._session_secret)


def session_requirement(gate: SessionGate) -> Callable[[Request], None]:
    def require_session(request: Request) -> None:
        if not gate.recognizes(request.cookies.get(SESSION_COOKIE)):
            raise ApiError(
                _UNAUTHORIZED,
                "session_required",
                "Esta sessão não foi aberta pelo arquivo de acesso da calculadora. Abra o "
                "arquivo indicado no terminal em que o comando qcalc serve está rodando.",
            )

    return require_session


def _matches(presented: str, expected: str) -> bool:
    return hmac.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))
