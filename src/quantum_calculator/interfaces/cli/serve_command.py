from typing import TextIO

from quantum_calculator.interfaces.api.server import (
    ServerAddress,
    ServerOptions,
    ServerStartError,
    serve,
)
from quantum_calculator.interfaces.cli.exit_codes import ExitCode


class ServeCommand:
    def __init__(self, stdout: TextIO, stderr: TextIO) -> None:
        self._stdout = stdout
        self._stderr = stderr

    def run(self, options: ServerOptions) -> ExitCode:
        if options.web_root is None:
            self._stderr.write(
                "qcalc: a interface web não acompanha esta instalação; só a API local fica "
                "disponível.\n"
            )
        try:
            serve(options, self._announce)
        except ServerStartError as error:
            self._stderr.write(f"qcalc: a bancada não foi iniciada: {error.reason}.\n")
            return ExitCode.SERVER_NOT_STARTED
        return ExitCode.SUCCESS

    def _announce(self, address: ServerAddress) -> None:
        self._stdout.write(
            f"Bancada em {address.url}\n"
            f"Arquivo de acesso: {address.launch_page}\n"
            "Abra o arquivo de acesso no navegador para entrar. Ctrl+C encerra a bancada.\n"
        )
        self._stdout.flush()
