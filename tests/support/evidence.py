from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

ENVIRONMENT_SECTION = "\nAmbiente\n"

_SUMMARY_PREFIX = "resultado "
_ASSIGNMENT = " = "


def scientific_content(document: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in document.items() if key != "environment"}


def before_environment(report: str) -> str:
    if ENVIRONMENT_SECTION not in report:
        raise ValueError("the report has no environment section")
    return report.split(ENVIRONMENT_SECTION)[0]


def declared_content(record: Any) -> dict[str, object]:
    result = record["result"]
    verification = record["verification"]
    return {
        **{
            key: record[key]
            for key in (
                "document",
                "schema_version",
                "input",
                "problem",
                "plan",
                "catalog",
                "constants",
                "units",
                "limitations",
            )
        },
        "status": verification["status"],
        "checks": [
            (check["identifier"], check["kind"], check["status"], check["statement"])
            for check in verification["checks"]
        ],
        "not_performed": verification["not_performed"],
        "references": verification["references"],
        "answers": [
            (
                answer["name"],
                answer["symbol"],
                answer["label"],
                answer["unit"],
                None if answer["estimate"] is None else answer["estimate"]["origin"],
            )
            for answer in result["answers"]
        ],
        "tables": [
            (
                table["name"],
                table["title"],
                table["rows"],
                [(column["name"], column["symbol"], column["unit"]) for column in table["columns"]],
            )
            for table in result["tables"]
        ],
        "effective": [(item["name"], item["label"]) for item in result["effective"]],
        "warnings": result["warnings"],
    }


@dataclass(frozen=True, slots=True)
class MeasuredSeries:
    name: str
    unit: str
    values: list[float]


def measured_series(record: Any) -> list[MeasuredSeries]:
    result = record["result"]
    series: list[MeasuredSeries] = []
    for answer in result["answers"]:
        name, unit = answer["name"], answer["unit"]
        series.append(MeasuredSeries(name, unit, [answer["value"]]))
        if answer["estimate"] is not None:
            series.append(MeasuredSeries(f"{name} estimate", unit, [answer["estimate"]["value"]]))
    for table in result["tables"]:
        series.extend(
            MeasuredSeries(f"{table['name']}.{column['name']}", column["unit"], column["values"])
            for column in table["columns"]
        )
    return series


def unit_scales(series: Iterable[MeasuredSeries]) -> dict[str, float]:
    scales: dict[str, float] = {}
    for measured in series:
        largest = max((abs(value) for value in measured.values), default=0.0)
        scales[measured.unit] = max(scales.get(measured.unit, 0.0), largest)
    return scales


def report_outline(report: str) -> list[str]:
    lines = report.splitlines()
    summary = next(index for index, line in enumerate(lines) if line.startswith(_SUMMARY_PREFIX))
    answered = [line.split(_ASSIGNMENT)[0] for line in lines[:summary]]
    headings = [line for line in lines[summary:] if line and not line.startswith(" ")]
    return answered + headings
