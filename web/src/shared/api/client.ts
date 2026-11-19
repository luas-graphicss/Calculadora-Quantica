import * as v from 'valibot'

import { apiErrorFrom, getDocument, parseDocument, readJson, request } from '@/shared/api/http'
import { answersSchema } from '@/shared/api/schemas/answers'
import { catalogSchema } from '@/shared/api/schemas/catalog'
import { comparisonSchema } from '@/shared/api/schemas/comparison'
import { type Rejection, rejectionSchema } from '@/shared/api/schemas/diagnostics'
import { type Interpretation, interpretationSchema } from '@/shared/api/schemas/records'
import {
  type Run,
  runDetailsSchema,
  runDocumentSchema,
  runListSchema,
} from '@/shared/api/schemas/run'
import { sampleTableSchema } from '@/shared/api/schemas/table'

const API = '/api/v1'
const NO_CONTENT = 204
const JSON_BODY = { 'Content-Type': 'application/json' }

export function fetchCatalog() {
  return getDocument(`${API}/catalog`, catalogSchema, 'o catálogo')
}

export async function fetchRuns(): Promise<Run[]> {
  const listed = await getDocument(`${API}/runs`, runListSchema, 'o histórico')
  return listed.runs
}

export function fetchRunDetails(identifier: string) {
  return getDocument(`${API}/runs/${identifier}`, runDetailsSchema, 'a execução')
}

export function fetchAnswers(identifier: string, unit: string | null) {
  const query = unit === null ? '' : `?${new URLSearchParams({ unit }).toString()}`
  return getDocument(`${API}/runs/${identifier}/answers${query}`, answersSchema, 'as respostas')
}

export function fetchTable(identifier: string, name: string) {
  return getDocument(`${API}/runs/${identifier}/tables/${name}`, sampleTableSchema, 'a tabela')
}

export function fetchComparison(base: string, other: string) {
  const query = new URLSearchParams({ base, other }).toString()
  return getDocument(`${API}/comparisons?${query}`, comparisonSchema, 'a comparação')
}

export async function hasSession(): Promise<boolean> {
  const response = await request(`${API}/session`)
  return response.status === NO_CONTENT
}

export function packageUrl(identifier: string): string {
  return `${API}/runs/${identifier}/package`
}

export function tableCsvUrl(identifier: string, name: string): string {
  return `${API}/runs/${identifier}/tables/${name}/csv`
}

export type ValidationOutcome =
  | { kind: 'interpretation'; interpretation: Interpretation }
  | { kind: 'rejection'; rejection: Rejection }

export async function validateInput(text: string, timeLimit: number): Promise<ValidationOutcome> {
  const query = new URLSearchParams({ time_limit: String(timeLimit) }).toString()
  const response = await request(`${API}/validations?${query}`, {
    method: 'POST',
    body: text,
    headers: JSON_BODY,
  })
  const payload = await readJson(response)
  const rejection = v.safeParse(rejectionSchema, payload)
  if (rejection.success) return { kind: 'rejection', rejection: rejection.output }
  if (!response.ok) throw apiErrorFrom(response.status, payload)
  return {
    kind: 'interpretation',
    interpretation: parseDocument(interpretationSchema, payload, 'a interpretação'),
  }
}

export type Submission = {
  text: string
  idempotencyKey: string
  timeLimit: number
  parent: string | null
}

export type SubmissionOutcome =
  { kind: 'accepted'; run: Run } | { kind: 'rejection'; rejection: Rejection }

export async function submitRun(submission: Submission): Promise<SubmissionOutcome> {
  const query = new URLSearchParams({ time_limit: String(submission.timeLimit) })
  if (submission.parent !== null) query.set('parent', submission.parent)
  const response = await request(`${API}/runs?${query.toString()}`, {
    method: 'POST',
    body: submission.text,
    headers: { ...JSON_BODY, 'Idempotency-Key': submission.idempotencyKey },
  })
  const payload = await readJson(response)
  const rejection = v.safeParse(rejectionSchema, payload)
  if (rejection.success) return { kind: 'rejection', rejection: rejection.output }
  if (!response.ok) throw apiErrorFrom(response.status, payload)
  return { kind: 'accepted', run: parseDocument(runDocumentSchema, payload, 'a submissão').run }
}

export async function cancelRun(identifier: string): Promise<Run> {
  const response = await request(`${API}/runs/${identifier}/cancellation`, { method: 'POST' })
  const payload = await readJson(response)
  if (!response.ok) throw apiErrorFrom(response.status, payload)
  return parseDocument(runDocumentSchema, payload, 'o cancelamento').run
}

export async function importPackage(content: Blob): Promise<Run> {
  const response = await request(`${API}/imports`, {
    method: 'POST',
    body: content,
    headers: { 'Content-Type': 'application/zip' },
  })
  const payload = await readJson(response)
  if (!response.ok) throw apiErrorFrom(response.status, payload)
  return parseDocument(runDocumentSchema, payload, 'a importação').run
}
