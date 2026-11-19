import * as v from 'valibot'

import { apiErrorSchema } from '@/shared/api/schemas/diagnostics'

const REQUEST_TIMEOUT_MS = 60_000

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    options?: ErrorOptions,
  ) {
    super(message, options)
    this.name = 'ApiError'
  }
}

export class UnexpectedResponseError extends Error {
  constructor(subject: string, options?: ErrorOptions) {
    super(`A resposta da bancada para ${subject} não tem o formato esperado.`, options)
    this.name = 'UnexpectedResponseError'
  }
}

type RequestOptions = {
  method?: 'GET' | 'POST'
  body?: BodyInit
  headers?: Record<string, string>
}

export function request(path: string, options: RequestOptions = {}): Promise<Response> {
  return fetch(path, {
    method: options.method ?? 'GET',
    body: options.body,
    headers: options.headers,
    credentials: 'same-origin',
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  })
}

export async function readJson(response: Response): Promise<unknown> {
  try {
    const payload: unknown = await response.json()
    return payload
  } catch (error) {
    if (error instanceof SyntaxError) return null
    throw error
  }
}

export function parseDocument<TSchema extends v.GenericSchema>(
  schema: TSchema,
  payload: unknown,
  subject: string,
): v.InferOutput<TSchema> {
  const parsed = v.safeParse(schema, payload)
  if (!parsed.success) {
    throw new UnexpectedResponseError(subject, { cause: parsed.issues })
  }
  return parsed.output
}

export function apiErrorFrom(status: number, payload: unknown): ApiError {
  const parsed = v.safeParse(apiErrorSchema, payload)
  if (parsed.success) {
    return new ApiError(status, parsed.output.code, parsed.output.message)
  }
  return new ApiError(status, `http_${status}`, `A bancada respondeu com o estado HTTP ${status}.`)
}

export async function getDocument<TSchema extends v.GenericSchema>(
  path: string,
  schema: TSchema,
  subject: string,
): Promise<v.InferOutput<TSchema>> {
  const response = await request(path)
  const payload = await readJson(response)
  if (!response.ok) throw apiErrorFrom(response.status, payload)
  return parseDocument(schema, payload, subject)
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError || error instanceof UnexpectedResponseError) return error.message
  if (error instanceof DOMException && error.name === 'TimeoutError') {
    return 'A bancada demorou demais para responder. Confira se o comando qcalc serve continua rodando.'
  }
  if (error instanceof TypeError) {
    return 'Não foi possível falar com a bancada. Confira se o comando qcalc serve continua rodando.'
  }
  return 'A operação falhou por um motivo inesperado.'
}
