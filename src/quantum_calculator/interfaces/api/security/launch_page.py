import html
import os
from pathlib import Path

from quantum_calculator.interfaces.api.documents import SESSION_PATH
from quantum_calculator.interfaces.api.security.loopback_guard import LOOPBACK_ADDRESS

LAUNCH_PAGE_NAME = "abrir-calculadora.html"

_OWNER_ONLY = 0o600
_PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Calculadora Quântica</title>
</head>
<body>
<form method="post" action="{action}">
<input type="hidden" name="code" value="{code}">
<p>A Calculadora Quântica está rodando nesta máquina.</p>
<button type="submit">Abrir a Calculadora Quântica</button>
</form>
<script>document.forms[0].submit()</script>
</body>
</html>
"""


def write_launch_page(directory: Path, port: int, launch_code: str) -> Path:
    path = directory / LAUNCH_PAGE_NAME
    path.unlink(missing_ok=True)
    page = _PAGE.format(
        action=html.escape(f"http://{LOOPBACK_ADDRESS}:{port}{SESSION_PATH}", quote=True),
        code=html.escape(launch_code, quote=True),
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _OWNER_ONLY)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(page)
    return path
