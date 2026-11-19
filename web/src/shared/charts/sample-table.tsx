import type { Column } from '@/shared/charts/series-groups'
import { unitLabel } from '@/shared/format/labels'
import { formatSample } from '@/shared/format/values'

type Props = {
  caption: string
  columns: readonly Column[]
}

const ROW_LIMIT = 200

export function SampleTable({ caption, columns }: Props) {
  const rowCount = Math.max(0, ...columns.map((column) => column.values.length))
  const shown = Math.min(rowCount, ROW_LIMIT)
  const rows = Array.from({ length: shown }, (_unused, row) => row)

  return (
    <div className="flex flex-col gap-2">
      <div
        role="region"
        aria-label={caption}
        tabIndex={0}
        className="max-h-96 overflow-auto border border-rule bg-surface"
      >
        <table className="w-full border-collapse text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.name}
                  scope="col"
                  className="sticky top-0 border-b border-rule-strong bg-surface px-3 py-2 text-right font-medium whitespace-nowrap"
                >
                  <span className="font-mono">{column.symbol}</span>
                  <span className="text-muted">{` (${unitLabel(column.unit)})`}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row} className="border-b border-rule last:border-b-0">
                {columns.map((column) => {
                  const value = column.values[row]
                  return (
                    <td
                      key={column.name}
                      className="px-3 py-1 text-right font-mono whitespace-nowrap tabular-nums"
                    >
                      {value === undefined ? '' : formatSample(value)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rowCount > shown ? (
        <p className="text-sm text-muted">
          {`A tabela mostra as primeiras ${shown} de ${rowCount} linhas. O arquivo CSV traz todas.`}
        </p>
      ) : null}
    </div>
  )
}
