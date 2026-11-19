import {
  type Draft,
  isRecord,
  literalText,
  numberLiteral,
  readPath,
} from '@/features/editor/input-document'

export type SymbolRow = {
  id: string
  name: string
  role: string
  domain: string
  unit: string
  argument: string
  value: string
}

const FUNCTION_ROLE = 'function'
const PARAMETER_ROLE = 'parameter'

export function blankSymbolRow(id: string): SymbolRow {
  return { id, name: '', role: '', domain: '', unit: '', argument: '', value: '' }
}

export type SymbolRows = {
  rows: SymbolRow[]
  issued: number
}

function rowIdentifier(issued: number): string {
  return `symbol-${issued}`
}

export function withBlankRow(table: SymbolRows): SymbolRows {
  return {
    rows: [...table.rows, blankSymbolRow(rowIdentifier(table.issued))],
    issued: table.issued + 1,
  }
}

export function symbolRowsFrom(draft: Draft): SymbolRows {
  const symbols = readPath(draft, ['symbols'])
  const declared = isRecord(symbols) ? Object.entries(symbols) : []
  const rows = declared.map(([name, description], index) => {
    const fields = isRecord(description) ? description : {}
    return {
      id: rowIdentifier(index),
      name,
      role: literalText(fields.role),
      domain: literalText(fields.domain),
      unit: literalText(fields.unit),
      argument: literalText(fields.argument),
      value: literalText(fields.value),
    }
  })
  const table = { rows, issued: rows.length }
  return rows.length === 0 ? withBlankRow(table) : table
}

export function takesArgument(row: SymbolRow): boolean {
  return row.role === FUNCTION_ROLE
}

export function takesValue(row: SymbolRow, symbolsCarryValues: boolean): boolean {
  return symbolsCarryValues && row.role === PARAMETER_ROLE
}

export function symbolsFromRows(
  rows: readonly SymbolRow[],
  symbolsCarryValues: boolean,
): Record<string, unknown> | undefined {
  const declared = new Map<string, Record<string, unknown>>()
  for (const row of rows) {
    const name = row.name.trim()
    if (name === '') continue
    const fields: Record<string, unknown> = {}
    if (row.role !== '') fields.role = row.role
    if (row.domain !== '') fields.domain = row.domain
    if (row.unit.trim() !== '') fields.unit = row.unit.trim()
    if (takesArgument(row) && row.argument.trim() !== '') fields.argument = row.argument.trim()
    const value = takesValue(row, symbolsCarryValues) ? numberLiteral(row.value) : undefined
    if (value !== undefined) fields.value = value
    declared.set(name, fields)
  }
  return declared.size === 0 ? undefined : Object.fromEntries(declared)
}
