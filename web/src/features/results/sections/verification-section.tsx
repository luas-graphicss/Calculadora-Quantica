import type { VerificationSection as Verification } from '@/shared/api/schemas/records'
import { SectionBlock } from '@/shared/components/section-block'
import { StatusStamp } from '@/shared/components/status-stamp'
import { describeCheckKind, describeVerification } from '@/shared/format/labels'

type Props = {
  verification: Verification
}

const PASSED = 'passed'

function countsSentence(checks: Verification['checks']): string {
  const counts = new Map<string, number>()
  for (const check of checks) {
    counts.set(check.status, (counts.get(check.status) ?? 0) + 1)
  }
  const parts = [...counts].map(
    ([status, count]) => `${count} ${describeVerification(status).label}${count > 1 ? 's' : ''}`,
  )
  return `${checks.length} checagens: ${parts.join(', ')}.`
}

export function VerificationSection({ verification }: Props) {
  const ordered = [
    ...verification.checks.filter((check) => check.status !== PASSED),
    ...verification.checks.filter((check) => check.status === PASSED),
  ]
  return (
    <SectionBlock title="Verificações">
      <div className="flex flex-wrap items-center gap-3">
        <StatusStamp prefix="verificação" status={describeVerification(verification.status)} />
        <p className="text-sm text-muted">{countsSentence(verification.checks)}</p>
      </div>
      <ul className="flex flex-col">
        {ordered.map((check) => (
          <li
            key={check.identifier}
            className="flex flex-col gap-2 border-b border-rule py-4 first:pt-0 last:border-b-0"
          >
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <StatusStamp status={describeVerification(check.status)} />
              <span className="text-sm text-muted">{describeCheckKind(check.kind)}</span>
              <code className="font-mono text-sm text-muted">{check.identifier}</code>
            </div>
            <p className="text-pretty">{check.statement}</p>
            {check.observed === null ? null : (
              <p className="text-sm text-pretty">
                <span className="text-muted">{'Observado: '}</span>
                {check.observed}
              </p>
            )}
          </li>
        ))}
      </ul>
      {verification.not_performed.length === 0 ? null : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Checagens não realizadas</h3>
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
            {verification.not_performed.map((item) => (
              <li key={item.identifier}>
                <code className="font-mono">{item.identifier}</code>
                {`: ${item.reason}`}
              </li>
            ))}
          </ul>
        </div>
      )}
      {verification.references.length === 0 ? null : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Referências</h3>
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
            {verification.references.map((reference) => (
              <li key={reference}>{reference}</li>
            ))}
          </ul>
        </div>
      )}
    </SectionBlock>
  )
}
