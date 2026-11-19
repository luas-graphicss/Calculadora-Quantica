from benchmarks.harness.report import (
    BenchmarkReport,
    RefusalMeasurement,
    TargetVerdict,
    WorkloadMeasurement,
)
from benchmarks.harness.stages import STAGE_LABELS

_GIBIBYTE = 1024**3
_MEBIBYTE = 1024**2
_COMPARISON_LABELS = {"relative": "relativo", "absolute": "absoluto"}


def render_summary(report: BenchmarkReport) -> str:
    lines = [
        f"Medição de desempenho: {report['software']['package']} {report['software']['version']}",
        f"Gerada em {report['generated_at']}",
        "",
        *_machine_lines(report),
        "",
        *_profile_lines(report),
        "",
        _protocol_line(report),
    ]
    for workload in report["workloads"]:
        lines += _workload_lines(workload)
    lines += ["", "Pedidos acima do perfil"]
    for refusal in report["refused_requests"]:
        lines += _refusal_lines(refusal)
    lines += ["", "Metas"]
    lines += [_target_line(verdict) for verdict in report["targets"]]
    return "\n".join(lines) + "\n"


def _machine_lines(report: BenchmarkReport) -> list[str]:
    machine = report["machine"]
    software = report["software"]
    limit = machine["memory_limit_bytes"]
    memory = f"{machine['memory_bytes'] / _GIBIBYTE:.2f} GiB"
    if limit is not None:
        memory += f"; limite do grupo de controle: {limit / _GIBIBYTE:.2f} GiB"
    threads = ", ".join(
        f"{name}={value}" for name, value in machine["linear_algebra_threads"].items()
    )
    libraries = "; ".join(
        f"{library['consumer']} {library['interface']}: {library['name']} {library['version']}"
        for library in software["linear_algebra"]
    )
    dependencies = ", ".join(
        f"{name} {version}" for name, version in software["dependencies"].items()
    )
    return [
        "Máquina",
        f"  CPU: {machine['cpu_model']}; {machine['logical_cpus']} CPUs lógicas; "
        f"{machine['architecture']}",
        f"  Memória: {memory}",
        f"  Sistema: {machine['operating_system']}; kernel {machine['kernel']}",
        f"  Python: {machine['python']}",
        f"  Threads de álgebra linear: {threads}",
        f"  BLAS e LAPACK: {libraries}",
        f"  Dependências: {dependencies}",
    ]


def _profile_lines(report: BenchmarkReport) -> list[str]:
    profile = report["profile"]
    reference = profile["machine"]
    lines = [
        f"Perfil de referência, congelado em {profile['frozen_on']}: "
        f"{reference['logical_cpus']} CPUs lógicas {reference['architecture']}, "
        f"{reference['memory_gibibytes']} GiB, {reference['operating_system']}, "
        f"{reference['python']}, uma execução por vez, "
        f"{profile['execution']['linear_algebra_threads']} thread de álgebra linear, "
        "sem cache de resultados"
    ]
    differences = report["profile_differences"]
    if not differences:
        return [*lines, "  Esta máquina corresponde ao perfil de referência."]
    lines.append("  Esta máquina não é o perfil de referência:")
    lines += [
        f"    {difference['attribute']}: {difference['found']} aqui, "
        f"{difference['reference']} no perfil"
        for difference in differences
    ]
    return lines


def _protocol_line(report: BenchmarkReport) -> str:
    protocol = report["profile"]["protocol"]
    return (
        f"Cargas, em segundos: {protocol['cold_runs']} execuções frias, "
        f"{protocol['warmup_runs']} aquecimentos e {protocol['measured_runs']} execuções medidas "
        "por percurso; percentil pelo posto mais próximo"
    )


def _workload_lines(workload: WorkloadMeasurement) -> list[str]:
    cold = workload["cold"]["summary"]
    warm = workload["warm"]["summary"]
    staged = workload["staged"]
    stages = "; ".join(
        f"{STAGE_LABELS[stage]} {timed['summary']['p50']:.4f} / {timed['summary']['p95']:.4f}"
        for stage, timed in staged["stages"].items()
    )
    total = staged["total"]["summary"]
    bench_peak = workload["warm"]["worker_peak_rss_bytes"] / _MEBIBYTE
    staged_peak = staged["worker_peak_rss_bytes"] / _MEBIBYTE
    precision = workload["precision"]
    worst = max(
        precision["answers"], key=lambda answer: answer["largest_deviation"] / answer["tolerance"]
    )
    return [
        "",
        f"  {workload['title']} [{workload['identifier']}]",
        f"    frio, qcalc solve em processo novo: p50 {cold['p50']:.3f}, máximo "
        f"{cold['maximum']:.3f}",
        f"    quente, bancada, do envio ao relatório: p50 {warm['p50']:.3f}, p95 "
        f"{warm['p95']:.3f}, máximo {warm['maximum']:.3f}",
        f"    estágios, p50 / p95: {stages}; soma {total['p50']:.4f} / {total['p95']:.4f}",
        f"    pico de memória do worker: {bench_peak:.1f} MiB na bancada, {staged_peak:.1f} MiB "
        "no percurso por estágios",
        f"    precisão: {precision['checked_records']} registros conferidos, verificação "
        f"{precision['verification']}; maior desvio {_COMPARISON_LABELS[worst['comparison']]} "
        f"{worst['largest_deviation']:.3e} em {worst['name']}, tolerância "
        f"{worst['tolerance']:.3e}",
    ]


def _refusal_lines(refusal: RefusalMeasurement) -> list[str]:
    lines = [
        f"  {refusal['title']} [{refusal['identifier']}]: código de saída "
        f"{refusal['exit_code']} em {refusal['seconds']:.3f} s"
    ]
    lines += [
        f"    {diagnostic.get('code')} em {diagnostic.get('pointer')}: {diagnostic.get('message')}"
        for diagnostic in refusal["diagnostics"]
    ]
    return lines


def _target_line(verdict: TargetVerdict) -> str:
    outcome = "atingida" if verdict["met"] else "não atingida"
    return (
        f"  {verdict['workload']}: p95 quente {verdict['warm_p95_seconds']:.3f} s, limite "
        f"{verdict['warm_p95_limit_seconds']:.3f} s; pico do worker "
        f"{verdict['worker_peak_rss_mebibytes']:.1f} MiB, limite "
        f"{verdict['worker_peak_rss_limit_mebibytes']} MiB: {outcome} nesta máquina"
    )
