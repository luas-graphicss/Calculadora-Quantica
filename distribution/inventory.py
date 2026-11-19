from distribution.documents import Manifest, PythonPackage

_PYPI = "https://pypi.org/project"


def render_inventory(manifest: Manifest) -> str:
    built_on = manifest["built_on"]
    lines = [
        "# Inventário de dependências e licenças",
        "",
        f"Distribuição offline de `{manifest['package']}` {manifest['version']}, montada em "
        f"{manifest['built_at']} para {built_on['operating_system']}, {built_on['architecture']}, "
        f"CPython {built_on['python']}. A calculadora é distribuída sob a GNU GPL versão 3; o "
        "texto de cada licença abaixo acompanha a distribuição na pasta `licenses/`.",
        "",
        "## Pacotes Python instalados",
        "",
        "Cada wheel é instalado do próprio pacote offline, com o hash conferido pelo instalador.",
        "",
        *_python_table(manifest["python_packages"]),
        "",
        "## Ferramenta de instalação",
        "",
        "Usada só para instalar; não entra no ambiente da calculadora.",
        "",
        *_python_table(manifest["installer_packages"]),
        "",
        "## Pacotes compilados na interface",
        "",
        "Entram nos arquivos estáticos servidos pelo `qcalc serve`; o usuário não instala Node.js.",
        "",
        "| Pacote | Versão | Licença |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| `{package['name']}` | {package['version']} | {package['license']} |"
        for package in manifest["interface_packages"]
    ]
    return "\n".join(lines) + "\n"


def _python_table(packages: list[PythonPackage]) -> list[str]:
    return [
        "| Pacote | Versão | Licença | Wheel | SHA-256 |",
        "| --- | --- | --- | --- | --- |",
        *(
            f"| [{package['name']}]({_PYPI}/{package['name']}/{package['version']}/) | "
            f"{package['version']} | {package['license']} | `{package['wheel']}` | "
            f"`{package['sha256']}` |"
            for package in packages
        ),
    ]
