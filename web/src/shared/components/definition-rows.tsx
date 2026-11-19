import type { ReactNode } from 'react'

export type DefinitionRow = {
  term: string
  description: ReactNode
}

type Props = {
  rows: readonly DefinitionRow[]
}

export function DefinitionRows({ rows }: Props) {
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm md:grid-cols-[minmax(10rem,16rem)_1fr]">
      {rows.map((row) => (
        <div key={row.term} className="contents">
          <dt className="text-muted">{row.term}</dt>
          <dd className="min-w-0 break-words">{row.description}</dd>
        </div>
      ))}
    </dl>
  )
}
