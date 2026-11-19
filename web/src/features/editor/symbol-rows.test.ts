import { describe, expect, it } from 'vitest'

import {
  blankSymbolRow,
  symbolRowsFrom,
  symbolsFromRows,
  withBlankRow,
} from '@/features/editor/symbol-rows'

describe('symbolRowsFrom', () => {
  it('opens one blank row for an input without symbols', () => {
    expect(symbolRowsFrom({})).toEqual({ rows: [blankSymbolRow('symbol-0')], issued: 1 })
  })

  it('reads each declared symbol into a row', () => {
    const table = symbolRowsFrom({
      symbols: {
        t: { role: 'variable', domain: 'real', unit: 's' },
        y: { role: 'function', domain: 'real', unit: '1', argument: 't' },
      },
    })

    expect(table.rows.map((row) => [row.name, row.role, row.unit, row.argument])).toEqual([
      ['t', 'variable', 's', ''],
      ['y', 'function', '1', 't'],
    ])
    expect(table.issued).toBe(2)
  })
})

describe('withBlankRow', () => {
  it('never reuses the identifier of a removed row', () => {
    const table = withBlankRow(symbolRowsFrom({}))
    const afterRemoval = { ...table, rows: table.rows.slice(1) }

    expect(withBlankRow(afterRemoval).rows.map((row) => row.id)).toEqual(['symbol-1', 'symbol-2'])
  })
})

describe('symbolsFromRows', () => {
  it('writes only the fields that were filled', () => {
    const rows = [
      { ...blankSymbolRow('a'), name: ' k ', role: 'parameter', unit: ' 1/s ' },
      blankSymbolRow('b'),
    ]
    expect(symbolsFromRows(rows, false)).toEqual({ k: { role: 'parameter', unit: '1/s' } })
  })

  it('keeps the argument only for a function', () => {
    const rows = [
      { ...blankSymbolRow('a'), name: 'y', role: 'function', argument: 't' },
      { ...blankSymbolRow('b'), name: 'k', role: 'parameter', argument: 't' },
    ]
    expect(symbolsFromRows(rows, false)).toEqual({
      y: { role: 'function', argument: 't' },
      k: { role: 'parameter' },
    })
  })

  it('keeps the value of a parameter only on cards whose symbols carry values', () => {
    const rows = [{ ...blankSymbolRow('a'), name: 'k', role: 'parameter', value: '0.5' }]
    expect(symbolsFromRows(rows, true)).toEqual({ k: { role: 'parameter', value: '0.5' } })
    expect(symbolsFromRows(rows, false)).toEqual({ k: { role: 'parameter' } })
  })

  it('declares nothing when every row is unnamed', () => {
    expect(symbolsFromRows([blankSymbolRow('a')], true)).toBeUndefined()
  })
})
