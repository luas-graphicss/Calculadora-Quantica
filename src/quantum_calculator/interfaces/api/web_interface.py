from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

_PACKAGED = Path(__file__).resolve().parent / "static"
_ENTRY_PAGE = "index.html"
_NOT_BUILT = (
    "A interface web não acompanha esta instalação: o diretório com os arquivos compilados "
    "não foi encontrado. A API local continua disponível em /api/v1.\n"
)


def packaged_interface() -> Path | None:
    return _PACKAGED if (_PACKAGED / _ENTRY_PAGE).is_file() else None


def mount_interface(app: FastAPI, web_root: Path | None) -> None:
    if web_root is not None and (web_root / _ENTRY_PAGE).is_file():
        app.mount("/", StaticFiles(directory=web_root, html=True), name="interface")
        return

    @app.get("/", include_in_schema=False)
    def interface_not_built() -> PlainTextResponse:
        return PlainTextResponse(_NOT_BUILT)
