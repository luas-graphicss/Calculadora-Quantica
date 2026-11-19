import signal
import socket
import webbrowser
from collections.abc import Callable
from contextlib import closing, suppress
from dataclasses import dataclass
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from quantum_calculator.interfaces.api.application import ApiSettings, create_api
from quantum_calculator.interfaces.api.security.launch_page import write_launch_page
from quantum_calculator.interfaces.api.security.loopback_guard import LOOPBACK_ADDRESS
from quantum_calculator.interfaces.api.security.session import SessionGate
from quantum_calculator.workbench_composition import Workbench, build_workbench


@dataclass(frozen=True, slots=True)
class ServerOptions:
    data_directory: Path
    port: int
    web_root: Path | None
    opens_browser: bool


@dataclass(frozen=True, slots=True)
class ServerAddress:
    port: int
    launch_page: Path

    @property
    def url(self) -> str:
        return f"http://{LOOPBACK_ADDRESS}:{self.port}"


class ServerStartError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def serve(options: ServerOptions, announce: Callable[[ServerAddress], None]) -> None:
    with closing(_listen_on_loopback(options.port)) as listener:
        port: int = listener.getsockname()[1]
        workbench = _open_workbench(options.data_directory)
        gate = SessionGate()
        api = create_api(workbench, gate, ApiSettings(port, options.web_root))
        launch_page = write_launch_page(options.data_directory, port, gate.launch_code)
        try:
            announce(ServerAddress(port, launch_page))
            if options.opens_browser:
                webbrowser.open(launch_page.as_uri())
            _run_until_stopped(api, listener)
        finally:
            launch_page.unlink(missing_ok=True)


def _run_until_stopped(api: FastAPI, listener: socket.socket) -> None:
    config = uvicorn.Config(api, log_level="warning", access_log=False, server_header=False)
    previous = signal.signal(signal.SIGTERM, signal.default_int_handler)
    try:
        with suppress(KeyboardInterrupt):
            uvicorn.Server(config).run(sockets=[listener])
    finally:
        signal.signal(signal.SIGTERM, previous)


def _listen_on_loopback(port: int) -> socket.socket:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((LOOPBACK_ADDRESS, port))
        listener.listen()
    except OSError as error:
        listener.close()
        raise ServerStartError(
            f"a porta {port} não pôde ser aberta em {LOOPBACK_ADDRESS} ({error.strerror})"
        ) from error
    return listener


def _open_workbench(data_directory: Path) -> Workbench:
    try:
        return build_workbench(data_directory)
    except OSError as error:
        raise ServerStartError(
            f"a pasta de dados {data_directory} não pôde ser usada ({error.strerror})"
        ) from error
