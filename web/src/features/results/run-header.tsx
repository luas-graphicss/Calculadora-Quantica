import { PackageOpen } from 'lucide-react'

import type { Run } from '@/shared/api/schemas/run'
import { textLink } from '@/shared/components/button-styles'
import { PageHeading } from '@/shared/components/page-heading'
import { StatusStamp } from '@/shared/components/status-stamp'
import { describeRunState, describeVerification } from '@/shared/format/labels'
import { formatInstant, shortIdentifier } from '@/shared/format/values'
import { RouteLink } from '@/shared/routing/route-link'

type Props = {
  run: Run
}

const IMPORTED = { label: 'importada', tone: 'neutral', icon: PackageOpen } as const

export function RunHeader({ run }: Props) {
  const parent = run.parent_identifier
  return (
    <PageHeading
      eyebrow={`Execução ${shortIdentifier(run.identifier)}, enviada em ${formatInstant(run.submitted_at)}`}
      title={run.card.title}
    >
      <div className="flex flex-wrap items-center gap-2">
        <StatusStamp status={describeRunState(run.state)} />
        {run.verification_status === null ? null : (
          <StatusStamp
            prefix="verificação"
            status={describeVerification(run.verification_status)}
          />
        )}
        {run.origin === 'imported' ? <StatusStamp status={IMPORTED} /> : null}
      </div>
      {parent === null ? null : (
        <p className="text-sm">
          {'Derivada da execução '}
          <RouteLink to={{ name: 'run', identifier: parent }} className={textLink}>
            {shortIdentifier(parent)}
          </RouteLink>
          {'. '}
          <RouteLink
            to={{ name: 'comparison', base: parent, other: run.identifier }}
            className={textLink}
          >
            Comparar com a execução de origem
          </RouteLink>
        </p>
      )}
    </PageHeading>
  )
}
