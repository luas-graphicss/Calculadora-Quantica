from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from quantum_calculator.interfaces.api.documents import SESSION_PATH
from quantum_calculator.interfaces.api.errors import refusal

LOOPBACK_ADDRESS = "127.0.0.1"

_LOOPBACK_NAMES = (LOOPBACK_ADDRESS, "localhost")
_OPAQUE_ORIGIN = "null"
_MISDIRECTED = 421
_FORBIDDEN = 403


class LoopbackGuard:
    def __init__(self, app: ASGIApp, port: int) -> None:
        self._app = app
        self._hosts = frozenset(f"{name}:{port}" for name in _LOOPBACK_NAMES)
        self._origins = frozenset(f"http://{host}" for host in self._hosts)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        if headers.get("host") not in self._hosts:
            rejection = refusal(
                _MISDIRECTED,
                "host_not_allowed",
                "A calculadora só atende pelo endereço local em que foi iniciada.",
            )
            await rejection(scope, receive, send)
            return
        if not self._accepts_origin(headers.get("origin"), scope):
            rejection = refusal(
                _FORBIDDEN,
                "origin_not_allowed",
                "A requisição veio de outra página; a calculadora só aceita a própria interface.",
            )
            await rejection(scope, receive, send)
            return
        await self._app(scope, receive, send)

    def _accepts_origin(self, origin: str | None, scope: Scope) -> bool:
        if origin is None or origin in self._origins:
            return True
        opens_session = scope["method"] == "POST" and scope["path"] == SESSION_PATH
        return opens_session and origin == _OPAQUE_ORIGIN
