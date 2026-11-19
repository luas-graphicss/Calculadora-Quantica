import { describe, expect, it } from 'vitest'

import { arrayText, parseArrayText } from '@/features/editor/array-text'

describe('arrayText', () => {
  it('writes a vector on one line and a matrix one row per line', () => {
    expect(arrayText([1, 0], 1)).toBe('[1,0]')
    expect(
      arrayText(
        [
          [1, 0],
          [0, -1],
        ],
        2,
      ),
    ).toBe('[\n  [1,0],\n  [0,-1]\n]')
  })

  it('is blank for a value that is not a list', () => {
    expect(arrayText(undefined, 1)).toBe('')
  })
})

describe('parseArrayText', () => {
  it('reads back what arrayText wrote', () => {
    const matrix = [
      [1, { real: 0, imaginary: 1 }],
      [0, -1],
    ]
    expect(parseArrayText(arrayText(matrix, 2))).toEqual({ ok: true, value: matrix })
  })

  it('treats a blank field as absent', () => {
    expect(parseArrayText('  ')).toEqual({ ok: true, value: undefined })
  })

  it('explains text that is not a list', () => {
    expect(parseArrayText('[1, 2')).toEqual({
      ok: false,
      message: 'O texto não é uma lista válida: confira colchetes e vírgulas.',
    })
    expect(parseArrayText('{"a": 1}')).toEqual({
      ok: false,
      message: 'Escreva uma lista entre colchetes.',
    })
  })
})
