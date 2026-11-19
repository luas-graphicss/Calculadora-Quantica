import type { Interpretation } from '@/shared/api/schemas/records'
import { PlanSummary } from '@/shared/record/plan-summary'
import { ProblemSummary } from '@/shared/record/problem-summary'

type Props = {
  interpretation: Interpretation
}

export function InterpretationPanel({ interpretation }: Props) {
  return (
    <div className="flex flex-col gap-6 border border-rule-strong bg-surface p-4 md:p-6">
      <ProblemSummary problem={interpretation.problem} />
      <div className="flex flex-col gap-2 border-t border-rule pt-5">
        <h3 className="text-sm font-semibold">Plano de cálculo</h3>
        <PlanSummary plan={interpretation.plan} />
      </div>
    </div>
  )
}
