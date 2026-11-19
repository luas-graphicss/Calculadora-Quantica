import type { CardForm } from '@/shared/api/schemas/catalog'

export type Draft = Readonly<Record<string, unknown>>
export type DraftPath = readonly string[]

export type ParsedDraft = { ok: true; draft: Draft } | { ok: false; message: string }

const INPUT_SCHEMA_VERSION = '1.0'
const DEFAULT_NOTATION = 'text'
const FORBIDDEN_KEYS = new Set(['__proto__', 'constructor', 'prototype'])
const INTEGER = /^-?\d{1,15}$/
const KEY_ORDER = [
  'schema_version',
  'problem',
  'description',
  'hypotheses',
  'parameters',
  'notation',
  'statement',
  'symbols',
  'equations',
  'conditions',
  'candidate',
  'initial_state',
  'state',
  'observable',
  'basis',
  'numerics',
  'requested',
  'uncertainty',
]

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function readPath(draft: Draft, path: DraftPath): unknown {
  let current: unknown = draft
  for (const key of path) {
    if (!isRecord(current) || !Object.hasOwn(current, key)) return undefined
    current = current[key]
  }
  return current
}

function withEntry(record: Draft, key: string, value: unknown): Draft {
  const entries = Object.entries(record)
  if (value === undefined) {
    return Object.fromEntries(entries.filter(([name]) => name !== key))
  }
  if (Object.hasOwn(record, key)) {
    return Object.fromEntries(
      entries.map(([name, current]) => [name, name === key ? value : current]),
    )
  }
  return Object.fromEntries([...entries, [key, value]])
}

export function writePath(draft: Draft, path: DraftPath, value: unknown): Draft {
  const [key, ...rest] = path
  if (key === undefined || FORBIDDEN_KEYS.has(key)) return draft
  if (rest.length === 0) return withEntry(draft, key, value)
  const child = draft[key]
  const nested = writePath(isRecord(child) ? child : {}, rest, value)
  return withEntry(draft, key, Object.keys(nested).length === 0 ? undefined : nested)
}

export function literalText(value: unknown): string {
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return typeof value === 'string' ? value : ''
}

export function textAt(draft: Draft, path: DraftPath): string {
  return literalText(readPath(draft, path))
}

export function numberLiteral(text: string): number | string | undefined {
  const trimmed = text.trim()
  if (trimmed === '') return undefined
  return INTEGER.test(trimmed) ? Number(trimmed) : trimmed
}

export function optionalText(text: string): string | undefined {
  return text.trim() === '' ? undefined : text
}

export function emptyDraft(card: string, form: CardForm): Draft {
  const identified: Draft = { schema_version: INPUT_SCHEMA_VERSION, problem: card }
  const notated =
    form.notation === null ? identified : { ...identified, notation: DEFAULT_NOTATION }
  const quantity = form.requested?.quantity ?? null
  return quantity === null ? notated : { ...notated, requested: { quantity } }
}

export function draftCard(draft: Draft): string | null {
  return typeof draft.problem === 'string' ? draft.problem : null
}

export function serializeDraft(draft: Draft): string {
  const known = KEY_ORDER.filter((key) => Object.hasOwn(draft, key))
  const others = Object.keys(draft)
    .filter((key) => !KEY_ORDER.includes(key))
    .sort()
  const ordered = Object.fromEntries([...known, ...others].map((key) => [key, draft[key]]))
  return `${JSON.stringify(ordered, null, 2)}\n`
}

export function parseDraft(text: string): ParsedDraft {
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch (error) {
    if (error instanceof SyntaxError) {
      return { ok: false, message: `O texto não é JSON válido: ${error.message}` }
    }
    throw error
  }
  if (!isRecord(parsed)) {
    return { ok: false, message: 'A entrada precisa ser um objeto JSON, entre chaves.' }
  }
  return { ok: true, draft: parsed }
}
