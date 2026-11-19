import type { Run } from '@/shared/api/schemas/run'
import { textLink } from '@/shared/components/button-styles'
import { StatusStamp } from '@/shared/components/status-stamp'
import { describeRunState, describeVerification } from '@/shared/format/labels'
import { formatInstant, shortIdentifier } from '@/shared/format/values'
import { RouteLink } from '@/shared/routing/route-link'

type Props = {
  side: string
  run: Run
}

export function ComparedRun({ side, run }: Props) {
  return (
    <div className="flex min-w-0 flex-col gap-2 border border-rule bg-surface p-4">
      <p className="text-xs font-semibold tracking-wide text-muted uppercase">{side}</p>
      <p className="font-medium text-pretty">
        <RouteLink to={{ name: 'run', identifier: run.identifier }} className={textLink}>
          {run.card.title}
        </RouteLink>
      </p>
      <p className="text-sm text-muted">
        {`Execução ${shortIdentifier(run.identifier)}, enviada em ${formatInstant(run.submitted_at)}`}
      </p>
      {run.headline === null ? null : <p className="font-mono break-words">{run.headline}</p>}
      <div className="flex flex-wrap gap-2">
        <StatusStamp status={describeRunState(run.state)} />
        {run.verification_status === null ? null : (
          <StatusStamp
            prefix="verificação"
            status={describeVerification(run.verification_status)}
          />
        )}
      </div>
    </div>
  )
}
