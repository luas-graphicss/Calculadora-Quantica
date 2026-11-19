import type { PlanSection } from '@/shared/api/schemas/records'
import { type DefinitionRow, DefinitionRows } from '@/shared/components/definition-rows'
import { describeNature } from '@/shared/format/labels'

type Props = {
  plan: PlanSection
}

const ROUNDING_MODES = new Map([['half_even', 'meio para o par mais próximo']])

export function describeRounding(rounding: NonNullable<PlanSection['rounding']>): string {
  const mode = ROUNDING_MODES.get(rounding.mode) ?? rounding.mode
  return `${rounding.significant_digits} algarismos significativos, ${mode}`
}

export function PlanSummary({ plan }: Props) {
  const rows: DefinitionRow[] = [
    { term: 'Método', description: <code className="font-mono">{plan.method}</code> },
    { term: 'Natureza da resposta', description: describeNature(plan.nature) },
    { term: 'Por que este método', description: plan.justification },
  ]
  if (plan.rounding !== undefined) {
    rows.push({ term: 'Arredondamento', description: describeRounding(plan.rounding) })
  }
  if (plan.budget !== undefined) {
    rows.push({ term: 'Limite de tempo', description: `${plan.budget.wall_seconds} s` })
  }
  return <DefinitionRows rows={rows} />
}
