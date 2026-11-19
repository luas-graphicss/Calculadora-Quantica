import type { ResultSection, RunRecord } from '@/shared/api/schemas/records'
import { SectionBlock } from '@/shared/components/section-block'
import { ProblemSummary } from '@/shared/record/problem-summary'

type Props = {
  record: RunRecord
}

type ConditionsProps = {
  title: string
  conditions: readonly { text: string }[]
}

function Conditions({ title, conditions }: ConditionsProps) {
  if (conditions.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      <ul className="flex list-disc flex-col gap-1 pl-5 font-mono text-sm">
        {conditions.map((condition) => (
          <li key={condition.text}>{condition.text}</li>
        ))}
      </ul>
    </div>
  )
}

type SpecialCasesProps = {
  cases: ResultSection['special_cases']
}

function SpecialCases({ cases }: SpecialCasesProps) {
  if (cases.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold">Casos especiais</h3>
      <ul className="flex list-disc flex-col gap-1 pl-5 font-mono text-sm">
        {cases.map((special) => (
          <li key={special.when.text}>{`se ${special.when.text}: ${special.answer.text}`}</li>
        ))}
      </ul>
    </div>
  )
}

export function ProblemSection({ record }: Props) {
  const { result } = record
  return (
    <SectionBlock title="Problema e hipóteses">
      <ProblemSummary problem={record.problem} />
      <Conditions title="A resposta vale quando" conditions={result.validity} />
      <Conditions title="A resposta supõe" conditions={result.assumptions} />
      <SpecialCases cases={result.special_cases} />
      {result.arbitrary_constants.length === 0 ? null : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Constantes arbitrárias</h3>
          <p className="font-mono text-sm">{result.arbitrary_constants.join(', ')}</p>
        </div>
      )}
    </SectionBlock>
  )
}
