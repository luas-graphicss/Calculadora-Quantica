import type { VerificationSection as Verification } from '@/shared/api/schemas/records'
import { Notice } from '@/shared/components/notice'
import { describeVerification } from '@/shared/format/labels'

type Props = {
  verification: Verification
}

const PASSED = 'passed'
const FAILED = 'failed'
const TITLES = new Map([
  [FAILED, 'A verificação reprovou este resultado'],
  ['inconclusive', 'A verificação não chegou a uma conclusão sobre este resultado'],
  ['conditional', 'Este resultado vale sob condição'],
])

export function VerdictNotice({ verification }: Props) {
  if (verification.status === PASSED) return null
  const unmet = verification.checks.filter((check) => check.status !== PASSED)
  const verdict = describeVerification(verification.status).label

  return (
    <Notice
      tone={verification.status === FAILED ? 'problem' : 'information'}
      title={TITLES.get(verification.status) ?? `Verificação ${verdict}`}
    >
      <ul className="flex flex-col gap-2">
        {unmet.map((check) => (
          <li key={check.identifier}>
            <span className="font-semibold">
              {`Checagem ${describeVerification(check.status).label}: `}
            </span>
            {check.statement}
            {check.observed === null ? null : ` Observado: ${check.observed}.`}
          </li>
        ))}
      </ul>
    </Notice>
  )
}
