import type { Run } from '@/shared/api/schemas/run'
import { textLink } from '@/shared/components/button-styles'
import { StatusStamp } from '@/shared/components/status-stamp'
import { describeRunState, describeTerm, describeVerification } from '@/shared/format/labels'
import { formatInstant } from '@/shared/format/values'
import { RouteLink } from '@/shared/routing/route-link'

type Props = {
  runs: readonly Run[]
  selected: readonly string[]
  selectionLimit: number
  onToggle: (identifier: string) => void
}

const HEADERS = [
  'Comparar',
  'Enviada em',
  'Problema',
  'Resposta',
  'Estado',
  'Verificação',
  'Origem',
]
const ABSENT = '—'

export function RunTable({ runs, selected, selectionLimit, onToggle }: Props) {
  return (
    <div role="region" aria-label="Execuções registradas" tabIndex={0} className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <caption className="sr-only">
          Execuções registradas, da mais recente para a mais antiga
        </caption>
        <thead>
          <tr className="border-b border-rule-strong">
            {HEADERS.map((header) => (
              <th
                key={header}
                scope="col"
                className="px-3 py-2 text-left font-medium whitespace-nowrap first:pl-0"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const isSelected = selected.includes(run.identifier)
            const submitted = formatInstant(run.submitted_at)
            return (
              <tr key={run.identifier} className="border-b border-rule align-top">
                <td className="py-2 pr-3">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    disabled={!isSelected && selected.length >= selectionLimit}
                    aria-label={`Comparar a execução de ${submitted}: ${run.card.title}`}
                    onChange={() => {
                      onToggle(run.identifier)
                    }}
                    className="size-4 accent-primary"
                  />
                </td>
                <td className="px-3 py-2 whitespace-nowrap tabular-nums">{submitted}</td>
                <td className="min-w-48 px-3 py-2">
                  <RouteLink to={{ name: 'run', identifier: run.identifier }} className={textLink}>
                    {run.card.title}
                  </RouteLink>
                </td>
                <td className="px-3 py-2 font-mono">{run.headline ?? ABSENT}</td>
                <td className="px-3 py-2">
                  <StatusStamp status={describeRunState(run.state)} />
                </td>
                <td className="px-3 py-2">
                  {run.verification_status === null ? (
                    ABSENT
                  ) : (
                    <StatusStamp status={describeVerification(run.verification_status)} />
                  )}
                </td>
                <td className="px-3 py-2">{describeTerm(run.origin)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
