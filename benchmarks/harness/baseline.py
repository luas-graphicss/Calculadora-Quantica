from benchmarks.harness.report import BenchmarkReport, WorkloadMeasurement

_MEBIBYTE = 1024**2
_MACHINE_ATTRIBUTES = ("cpu_model", "logical_cpus", "memory_bytes", "operating_system", "python")


def render_comparison(baseline: BenchmarkReport, candidate: BenchmarkReport) -> str:
    lines = [
        "Comparação com a linha de base congelada",
        f"  linha de base: {_origin(baseline)}",
        f"  candidata: {_origin(candidate)}",
        _machine_line(baseline, candidate),
    ]
    measured = {workload["identifier"]: workload for workload in candidate["workloads"]}
    for before in baseline["workloads"]:
        after = measured.get(before["identifier"])
        if after is None:
            lines.append(f"  {before['identifier']}: ausente da medição candidata")
            continue
        lines += _workload_lines(before, after)
    return "\n".join(lines) + "\n"


def _origin(report: BenchmarkReport) -> str:
    software = report["software"]
    return f"{software['package']} {software['version']}, gerada em {report['generated_at']}"


def _machine_line(baseline: BenchmarkReport, candidate: BenchmarkReport) -> str:
    is_same = all(
        baseline["machine"][attribute] == candidate["machine"][attribute]  # type: ignore[literal-required]  # the names are keys of Machine
        for attribute in _MACHINE_ATTRIBUTES
    )
    if is_same:
        return "  mesma CPU, memória, sistema e Python nas duas medições"
    return (
        "  as medições vêm de máquinas diferentes: a razão entre os tempos não mede só a "
        "mudança de código"
    )


def _workload_lines(before: WorkloadMeasurement, after: WorkloadMeasurement) -> list[str]:
    stages = "; ".join(
        f"{stage} {timed['summary']['p50']:.4f} -> "
        f"{after['staged']['stages'][stage]['summary']['p50']:.4f}"
        for stage, timed in before["staged"]["stages"].items()
    )
    return [
        "",
        f"  {before['title']} [{before['identifier']}]",
        "    frio p50: "
        + _change(before["cold"]["summary"]["p50"], after["cold"]["summary"]["p50"]),
        "    quente p50: "
        + _change(before["warm"]["summary"]["p50"], after["warm"]["summary"]["p50"]),
        "    quente p95: "
        + _change(before["warm"]["summary"]["p95"], after["warm"]["summary"]["p95"]),
        f"    estágios p50: {stages}",
        f"    pico do worker na bancada: {before['warm']['worker_peak_rss_bytes'] / _MEBIBYTE:.1f}"
        f" -> {after['warm']['worker_peak_rss_bytes'] / _MEBIBYTE:.1f} MiB",
    ]


def _change(before: float, after: float) -> str:
    return f"{before:.3f} -> {after:.3f} s ({after / before:.2f} vezes)"
