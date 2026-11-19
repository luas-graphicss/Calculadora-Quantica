import type { ReactNode } from 'react'

export type TableRow = {
  key: string
  cells: readonly ReactNode[]
}

type Props = {
  caption: string
  headers: readonly string[]
  rows: readonly TableRow[]
}

export function SimpleTable({ caption, headers, rows }: Props) {
  return (
    <div role="region" aria-label={caption} tabIndex={0} className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-rule-strong">
            {headers.map((header) => (
              <th key={header} scope="col" className="px-3 py-2 text-left font-medium first:pl-0">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key} className="border-b border-rule align-top">
              {row.cells.map((cell, index) => (
                <td key={headers[index] ?? index} className="px-3 py-2 first:pl-0">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
