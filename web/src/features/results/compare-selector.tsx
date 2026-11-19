import { useState } from 'react'

import { useRuns } from '@/shared/api/queries'
import type { Run } from '@/shared/api/schemas/run'
import { secondaryButton } from '@/shared/components/button-styles'
import { SelectField } from '@/shared/components/select-field'
import { describeRunState } from '@/shared/format/labels'
import { formatInstant } from '@/shared/format/values'
import { RouteLink } from '@/shared/routing/route-link'

type Props = {
  run: Run
}

function describeOther(other: Run): string {
  const outcome = other.headline ?? describeRunState(other.state).label
  return `${formatInstant(other.submitted_at)} · ${other.card.title} · ${outcome}`
}

export function CompareSelector({ run }: Props) {
  const runs = useRuns()
  const [chosen, setChosen] = useState('')
  const others = (runs.data ?? []).filter((other) => other.identifier !== run.identifier)
  const base = chosen === '' ? (run.parent_identifier ?? '') : chosen
  const isListed = others.some((other) => other.identifier === base)

  if (others.length === 0) {
    return <p className="text-sm text-muted">Não há outra execução no histórico para comparar.</p>
  }
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-end">
      <div className="min-w-0 flex-1">
        <SelectField
          label="Comparar com a execução"
          value={isListed ? base : ''}
          placeholder="escolha uma execução"
          options={others.map((other) => ({
            value: other.identifier,
            label: describeOther(other),
          }))}
          onChange={setChosen}
        />
      </div>
      {isListed ? (
        <RouteLink
          to={{ name: 'comparison', base, other: run.identifier }}
          className={secondaryButton}
        >
          Comparar
        </RouteLink>
      ) : null}
    </div>
  )
}
