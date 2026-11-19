import { ActiveRunPanel } from '@/features/results/active-run-panel'
import { EndedWithoutResult } from '@/features/results/ended-without-result'
import { RecordView } from '@/features/results/record-view'
import { ResubmitButton } from '@/features/results/resubmit-button'
import { RunHeader } from '@/features/results/run-header'
import { readInterpretation, readOutcome } from '@/features/results/run-outcome'
import { ReproductionSection } from '@/features/results/sections/reproduction-section'
import { isActive, type RunDetails } from '@/shared/api/schemas/run'
import { Notice } from '@/shared/components/notice'
import { SectionBlock } from '@/shared/components/section-block'
import { describeRunState } from '@/shared/format/labels'
import { PlanSummary } from '@/shared/record/plan-summary'
import { ProblemSummary } from '@/shared/record/problem-summary'

type Props = {
  details: RunDetails
}

export function RunView({ details }: Props) {
  const { run } = details
  const outcome = readOutcome(details.outcome)
  const interpretation = outcome.kind === 'record' ? null : readInterpretation(details.problem)

  return (
    <div className="flex flex-col gap-8">
      <RunHeader run={run} />
      <p role="status" className="sr-only">
        {`Estado da execução: ${describeRunState(run.state).label}.`}
      </p>
      {run.origin === 'imported' ? (
        <div className="flex flex-col gap-3">
          <Notice tone="information" title="Execução importada de um pacote">
            Os valores abaixo são os que o pacote registra. Nada foi recalculado nesta instalação.
          </Notice>
          <ResubmitButton details={details} label="Reexecutar nesta instalação" />
        </div>
      ) : null}
      {isActive(run) ? <ActiveRunPanel run={run} /> : null}
      {outcome.kind === 'record' ? <RecordView details={details} record={outcome.record} /> : null}
      {outcome.kind === 'record' || isActive(run) ? null : (
        <EndedWithoutResult details={details} outcome={outcome} />
      )}
      {interpretation === null ? null : (
        <SectionBlock title="Problema enviado">
          <ProblemSummary problem={interpretation.problem} />
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold">Plano de cálculo</h3>
            <PlanSummary plan={interpretation.plan} />
          </div>
        </SectionBlock>
      )}
      <ReproductionSection
        details={details}
        record={outcome.kind === 'record' ? outcome.record : null}
      />
    </div>
  )
}
