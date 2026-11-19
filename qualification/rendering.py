from collections.abc import Sequence

from qualification.documents import (
    CardCoverage,
    CaseMatrix,
    Expectation,
    MatrixCase,
    Observation,
    ReproductionReport,
)

_FAMILY_TITLES = {
    "quantum": "Fichas de expressão fechada",
    "symbolic": "Enunciados digitados",
    "numerical": "Métodos numéricos",
    "notation": "Corpus de notação",
}
_AGREES = "confere"


def render_matrix(matrix: CaseMatrix) -> str:
    cases = matrix["cases"]
    diverging = sum(1 for case in cases if case["disagreements"])
    gaps = sum(1 for coverage in matrix["coverage"] if coverage["gaps"])
    lines = [
        "# Matriz de casos da homologação",
        "",
        f"Gerada em {matrix['generated_at']} por `{matrix['calculator']}`, com o catálogo "
        f"{matrix['catalog_version']}. Cada linha roda uma entrada do corpus pelo comando "
        "`qcalc` e compara o que saiu com o oráculo de `reference_cases/`, escrito sem chamar "
        "o método que ele confere.",
        "",
        f"{len(cases)} casos, {diverging} com divergência; {len(matrix['coverage'])} fichas, "
        f"{gaps} com lacuna de cobertura.",
    ]
    for family, title in _FAMILY_TITLES.items():
        lines += _family_lines(title, [c for c in cases if c["expectation"]["family"] == family])
    lines += _coverage_lines(matrix["coverage"])
    return "\n".join(lines) + "\n"


def render_reproduction(report: ReproductionReport) -> str:
    cases = report["cases"]
    diverging = [case for case in cases if case["differences"]]
    homologated = report["homologated"]
    lines = [
        f"Reprodução do corpus por {report['calculator']}, em {report['generated_at']}",
        f"Homologação de referência: {homologated['calculator']}, catálogo "
        f"{homologated['catalog_version']}, em {homologated['generated_at']}",
        f"Ambiente: {_environment(report['environment'])}",
        f"Casos reproduzidos: {len(cases) - len(diverging)} de {len(cases)}",
    ]
    lines += [f"  {case['identifier']}: {'; '.join(case['differences'])}" for case in diverging]
    lines.append(
        "Catálogo: "
        + ("; ".join(report["catalog_differences"]) or "as mesmas fichas, versões e métodos")
    )
    for package in report["packages"]:
        outcome = "; ".join(package["differences"]) or "reproduzido"
        divergences = ", ".join(
            f"{divergence['subject']} {divergence['base']} -> {divergence['other']}"
            for divergence in package["version_divergences"]
        )
        lines.append(
            f"Pacote {package['package']} (sha256 {package['sha256']}): importado como "
            f"{package['imported_state']}, reexecução {package['rerun_state']}: {outcome}"
        )
        lines.append(f"  versões diferentes das do pacote: {divergences or 'nenhuma'}")
        lines.append(
            f"  reexecução exportada e importada em outra bancada: {package['received_state']}"
        )
    return "\n".join(lines) + "\n"


def _family_lines(title: str, cases: Sequence[MatrixCase]) -> list[str]:
    lines = [
        "",
        f"## {title}",
        "",
        "| Caso | Ficha | Oráculo | Esperado | Observado | Resultado |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines += [
        "| "
        + " | ".join(
            _cell(text)
            for text in (
                f"`{case['expectation']['identifier']}`",
                f"`{case['expectation']['card']}`" if case["expectation"]["card"] else "",
                case["expectation"]["oracle"],
                _expected(case["expectation"]),
                _observed(case["expectation"], case["observation"]),
                _outcome(case["disagreements"]),
            )
        )
        + " |"
        for case in cases
    ]
    return lines


def _coverage_lines(coverage: Sequence[CardCoverage]) -> list[str]:
    lines = [
        "",
        "## Cobertura por ficha",
        "",
        "Cada ficha anunciada precisa de um exemplo reexecutável com oráculo independente e de "
        "ao menos uma entrada recusada, que mostra o comportamento fora do domínio.",
        "",
        "| Ficha | Versão | Método | Exemplo | Casos respondidos | Casos recusados | Lacunas |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines += [
        "| "
        + " | ".join(
            _cell(text)
            for text in (
                f"`{card['card']}`",
                card["version"],
                f"`{card['method']}`",
                f"`{card['example']}`",
                str(len(card["answered_cases"])),
                str(len(card["refused_cases"])),
                "; ".join(card["gaps"]) or "nenhuma",
            )
        )
        + " |"
        for card in coverage
    ]
    return lines


def _expected(expectation: Expectation) -> str:
    parts = [
        f"{value['name']} = {value['expected']!r} ± {value['tolerance']:g}"
        + (" relativo" if value["comparison"] == "relative" else "")
        for value in expectation["values"]
    ]
    parts += [f"{name}: `{text}`" for name, text in expectation["texts"].items()]
    if expectation["verification"] is not None:
        parts.append(_verdict(expectation["verification"], expectation["not_passed"]))
    refusal = expectation["refusal"]
    if refusal is not None:
        parts.append(f"recusa {refusal['category']}/{refusal['code']} em `{refusal['pointer']}`")
    return "; ".join([*parts, f"código {expectation['exit_code']}"])


def _observed(expectation: Expectation, observation: Observation) -> str:
    named = [value["name"] for value in expectation["values"]]
    parts = [
        f"{name} = {observation['values'][name]!r}"
        for name in named
        if name in observation["values"]
    ]
    parts += [f"{name}: `{text}`" for name, text in observation["texts"].items()]
    if observation["verification"] is not None:
        parts.append(_verdict(observation["verification"], observation["not_passed"]))
    parts += [
        f"recusa {refusal['category']}/{refusal['code']} em `{refusal['pointer']}`"
        for refusal in observation["refusals"]
    ]
    return "; ".join([*parts, f"código {observation['exit_code']}"])


def _verdict(verification: str, not_passed: Sequence[str]) -> str:
    if not not_passed:
        return f"verificação {verification}"
    return f"verificação {verification}, sem aprovar {', '.join(not_passed)}"


def _outcome(disagreements: Sequence[str]) -> str:
    return "diverge: " + "; ".join(disagreements) if disagreements else _AGREES


def _environment(environment: dict[str, object]) -> str:
    described = [
        f"{environment.get('python_implementation')} {environment.get('python_version')}",
        str(environment.get("platform")),
    ]
    dependencies = environment.get("dependencies")
    if isinstance(dependencies, list):
        described += [f"{entry.get('name')} {entry.get('version')}" for entry in dependencies]
    return ", ".join(described)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")
