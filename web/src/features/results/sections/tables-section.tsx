import { SampleTableView } from '@/features/results/sections/sample-table-view'
import type { TableOutline } from '@/shared/api/schemas/records'
import { SectionBlock } from '@/shared/components/section-block'

type Props = {
  identifier: string
  tables: readonly TableOutline[]
}

export function TablesSection({ identifier, tables }: Props) {
  return (
    <SectionBlock title="Tabelas e séries">
      <div className="flex flex-col gap-10">
        {tables.map((outline) => (
          <SampleTableView key={outline.name} identifier={identifier} outline={outline} />
        ))}
      </div>
    </SectionBlock>
  )
}
