import { useId } from 'react'

import { tableCsvUrl } from '@/shared/api/client'
import { useTable } from '@/shared/api/queries'
import type { TableOutline } from '@/shared/api/schemas/records'
import { LineChart } from '@/shared/charts/line-chart'
import { SampleTable } from '@/shared/charts/sample-table'
import { seriesGroups } from '@/shared/charts/series-groups'
import { textLink } from '@/shared/components/button-styles'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { unitLabel } from '@/shared/format/labels'

type Props = {
  identifier: string
  outline: TableOutline
}

export function SampleTableView({ identifier, outline }: Props) {
  const headingId = useId()
  const table = useTable(identifier, outline.name)
  const groups = table.data === undefined ? [] : seriesGroups(table.data.columns)
  const columns = outline.columns
    .map((column) => `${column.symbol} (${unitLabel(column.unit)})`)
    .join(', ')

  return (
    <article aria-labelledby={headingId} className="flex flex-col gap-3">
      <h3 id={headingId} className="text-base font-medium text-pretty">
        {outline.title}
      </h3>
      <p className="text-sm text-muted">{`${outline.rows} linhas. Colunas: ${columns}.`}</p>
      {table.error === undefined ? null : <ErrorNotice error={table.error} />}
      {table.data === undefined && table.error === undefined ? (
        <LoadingLine label="Carregando a tabela" />
      ) : null}
      {groups.map((group) => (
        <LineChart key={group.unit} group={group} />
      ))}
      {table.data === undefined ? null : groups.length === 0 ? (
        <SampleTable caption={outline.title} columns={table.data.columns} />
      ) : (
        <details>
          <summary className="cursor-pointer text-sm font-medium">Dados em tabela</summary>
          <div className="pt-3">
            <SampleTable caption={outline.title} columns={table.data.columns} />
          </div>
        </details>
      )}
      <p>
        <a href={tableCsvUrl(identifier, outline.name)} download className={`${textLink} text-sm`}>
          Baixar CSV com unidades
          <span className="sr-only">{`: ${outline.title}`}</span>
        </a>
      </p>
    </article>
  )
}
