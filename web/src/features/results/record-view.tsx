import { useState } from 'react'

import { AnswerBlock } from '@/features/results/answer-block'
import { LimitationsSection } from '@/features/results/sections/limitations-section'
import { MethodSection } from '@/features/results/sections/method-section'
import { PrecisionSection } from '@/features/results/sections/precision-section'
import { ProblemSection } from '@/features/results/sections/problem-section'
import { TablesSection } from '@/features/results/sections/tables-section'
import { VerificationSection } from '@/features/results/sections/verification-section'
import { useAnswers } from '@/shared/api/queries'
import type { RunRecord } from '@/shared/api/schemas/records'
import type { RunDetails } from '@/shared/api/schemas/run'

type Props = {
  details: RunDetails
  record: RunRecord
}

export function RecordView({ details, record }: Props) {
  const [unit, setUnit] = useState<string | null>(null)
  const { identifier } = details.run
  const answers = useAnswers(identifier, unit, true)

  return (
    <>
      <AnswerBlock
        record={record}
        answers={answers.data}
        answersError={answers.error}
        displayUnits={details.display_units}
        unit={unit}
        onUnitChange={setUnit}
      />
      <ProblemSection record={record} />
      <MethodSection record={record} />
      <PrecisionSection record={record} answers={answers.data?.answers ?? []} />
      <VerificationSection verification={record.verification} />
      {record.result.tables.length === 0 ? null : (
        <TablesSection identifier={identifier} tables={record.result.tables} />
      )}
      {record.limitations.length === 0 ? null : (
        <LimitationsSection limitations={record.limitations} />
      )}
    </>
  )
}
