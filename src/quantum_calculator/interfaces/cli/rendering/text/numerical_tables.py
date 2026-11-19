from quantum_calculator.domain.numerical.report import SampleColumn, SampleTable
from quantum_calculator.domain.rounding import render_float
from quantum_calculator.interfaces.cli.rendering.text.formatting import section

DIMENSIONLESS_UNIT = "1"

_FULL_TABLE_ROWS = 64
_PREVIEW_ROWS = 17
_COLUMN_GAP = "  "


def with_unit(value: str, unit: str) -> str:
    return value if unit == DIMENSIONLESS_UNIT else f"{value} {unit}"


def table_sections(tables: tuple[SampleTable, ...], significant_digits: int) -> list[str]:
    lines: list[str] = []
    for table in tables:
        title = f"Tabela {table.name}: {table.title}"
        lines += section(title, _table_lines(table, significant_digits))
    return lines


def _table_lines(table: SampleTable, significant_digits: int) -> list[str]:
    rows = _shown_rows(table.row_count)
    headers = [_header(column) for column in table.columns]
    cells = [
        [str(render_float(column.values[row], significant_digits)) for column in table.columns]
        for row in rows
    ]
    widths = [
        max([len(header), *(len(line[index]) for line in cells)])
        for index, header in enumerate(headers)
    ]
    lines = [_aligned(headers, widths), *(_aligned(line, widths) for line in cells)]
    if len(rows) < table.row_count:
        lines.append(
            f"{table.row_count} linhas; mostradas {len(rows)}, igualmente espaçadas. "
            "A tabela completa sai com --format json."
        )
    return lines


def _shown_rows(count: int) -> list[int]:
    if count <= _FULL_TABLE_ROWS:
        return list(range(count))
    last = count - 1
    return sorted({round(index * last / (_PREVIEW_ROWS - 1)) for index in range(_PREVIEW_ROWS)})


def _header(column: SampleColumn) -> str:
    if column.unit == DIMENSIONLESS_UNIT:
        return column.symbol
    return f"{column.symbol} [{column.unit}]"


def _aligned(cells: list[str], widths: list[int]) -> str:
    padded = (cell.ljust(width) for cell, width in zip(cells, widths, strict=True))
    return _COLUMN_GAP.join(padded).rstrip()
