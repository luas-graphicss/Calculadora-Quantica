import * as v from 'valibot'

export const RUN_STATES = [
  'queued',
  'running',
  'succeeded',
  'failed',
  'cancelled',
  'interrupted',
] as const

export type RunState = (typeof RUN_STATES)[number]

export const runSchema = v.object({
  identifier: v.string(),
  origin: v.picklist(['local', 'imported']),
  state: v.picklist(RUN_STATES),
  parent_identifier: v.nullable(v.string()),
  card: v.object({ identifier: v.string(), title: v.string() }),
  wall_seconds: v.number(),
  package_version: v.string(),
  submitted_at: v.string(),
  started_at: v.nullable(v.string()),
  finished_at: v.nullable(v.string()),
  verification_status: v.nullable(v.string()),
  failure_category: v.nullable(v.string()),
  headline: v.nullable(v.string()),
  input_sha256: v.string(),
  canonical_problem_sha256: v.string(),
})

export type Run = v.InferOutput<typeof runSchema>

export const runDocumentSchema = v.object({ run: runSchema })

export const runListSchema = v.object({ runs: v.array(runSchema) })

export const runDetailsSchema = v.object({
  run: runSchema,
  input: v.object({ text: v.string() }),
  problem: v.unknown(),
  outcome: v.unknown(),
  display_units: v.array(v.string()),
})

export type RunDetails = v.InferOutput<typeof runDetailsSchema>

export function isActive(run: Run): boolean {
  return run.state === 'queued' || run.state === 'running'
}
