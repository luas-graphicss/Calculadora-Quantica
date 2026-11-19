import { useState } from 'react'

import { ImportPackageButton } from '@/features/history/import-package-button'
import { RunTable } from '@/features/history/run-table'
import { useRuns } from '@/shared/api/queries'
import type { Run } from '@/shared/api/schemas/run'
import { secondaryButton, textLink } from '@/shared/components/button-styles'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { PageHeading } from '@/shared/components/page-heading'
import { usePageTitle } from '@/shared/hooks/use-page-title'
import { RouteLink } from '@/shared/routing/route-link'

const COMPARED_RUNS = 2

function inSubmissionOrder(runs: readonly Run[], selected: readonly string[]): Run[] {
  return runs
    .filter((run) => selected.includes(run.identifier))
    .sort((first, second) => first.submitted_at.localeCompare(second.submitted_at))
}

export function HistoryPage() {
  usePageTitle('Histórico')
  const runs = useRuns()
  const [selected, setSelected] = useState<readonly string[]>([])
  const [base, other] = inSubmissionOrder(runs.data ?? [], selected)

  function toggle(identifier: string) {
    setSelected((current) =>
      current.includes(identifier)
        ? current.filter((item) => item !== identifier)
        : [...current, identifier],
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeading title="Histórico" />
      <div className="flex flex-wrap items-start gap-3">
        <ImportPackageButton />
        {base !== undefined && other !== undefined ? (
          <RouteLink
            to={{ name: 'comparison', base: base.identifier, other: other.identifier }}
            className={secondaryButton}
          >
            Comparar as duas selecionadas
          </RouteLink>
        ) : null}
      </div>
      {runs.error === undefined ? null : <ErrorNotice error={runs.error} />}
      {runs.data === undefined && runs.error === undefined ? (
        <LoadingLine label="Carregando o histórico" />
      ) : null}
      {runs.data?.length === 0 ? (
        <p>
          {'Nenhuma execução registrada. '}
          <RouteLink to={{ name: 'catalog' }} className={textLink}>
            Formular um problema
          </RouteLink>
        </p>
      ) : null}
      {runs.data === undefined || runs.data.length === 0 ? null : (
        <>
          <p className="text-sm text-muted">Marque duas execuções para comparar.</p>
          <RunTable
            runs={runs.data}
            selected={selected}
            selectionLimit={COMPARED_RUNS}
            onToggle={toggle}
          />
        </>
      )}
    </div>
  )
}
