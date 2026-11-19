import * as v from 'valibot'

import {
  calculationFailureSchema,
  type Rejection,
  rejectionSchema,
} from '@/shared/api/schemas/diagnostics'
import {
  type Interpretation,
  interpretationSchema,
  type RunRecord,
  runRecordSchema,
} from '@/shared/api/schemas/records'

export type RunOutcome =
  | { kind: 'none' }
  | { kind: 'record'; record: RunRecord }
  | { kind: 'rejection'; rejection: Rejection }
  | { kind: 'failure'; message: string }
  | { kind: 'unreadable' }

export function readOutcome(outcome: unknown): RunOutcome {
  if (outcome === null || outcome === undefined) return { kind: 'none' }
  const record = v.safeParse(runRecordSchema, outcome)
  if (record.success) return { kind: 'record', record: record.output }
  const rejection = v.safeParse(rejectionSchema, outcome)
  if (rejection.success) return { kind: 'rejection', rejection: rejection.output }
  const failure = v.safeParse(calculationFailureSchema, outcome)
  if (failure.success) return { kind: 'failure', message: failure.output.message }
  return { kind: 'unreadable' }
}

export function readInterpretation(problem: unknown): Interpretation | null {
  const parsed = v.safeParse(interpretationSchema, problem)
  return parsed.success ? parsed.output : null
}
