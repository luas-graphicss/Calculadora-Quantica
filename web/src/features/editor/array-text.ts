export type ParsedArray =
  { ok: true; value: unknown[] | undefined } | { ok: false; message: string }

const MATRIX_RANK = 2

export function arrayText(value: unknown, rank: number): string {
  if (!Array.isArray(value)) return ''
  if (rank < MATRIX_RANK) return JSON.stringify(value)
  const rows = value.map((row) => `  ${JSON.stringify(row)}`)
  return `[\n${rows.join(',\n')}\n]`
}

export function parseArrayText(text: string): ParsedArray {
  if (text.trim() === '') return { ok: true, value: undefined }
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch (error) {
    if (error instanceof SyntaxError) {
      return { ok: false, message: 'O texto não é uma lista válida: confira colchetes e vírgulas.' }
    }
    throw error
  }
  if (!Array.isArray(parsed)) {
    return { ok: false, message: 'Escreva uma lista entre colchetes.' }
  }
  return { ok: true, value: parsed }
}
