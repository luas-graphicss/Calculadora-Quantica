import { describe, expect, it } from 'vitest'

import type { CardForm } from '@/shared/api/schemas/catalog'
import { describePointer } from '@/shared/format/pointers'

const FORM: CardForm = {
  kind: 'numerical',
  confirmations: [],
  quantities: [
    {
      name: 'width',
      symbol: 'L',
      label: 'largura do poço',
      dimension: 'comprimento',
      units: ['m', 'nm'],
      constants: [],
    },
  ],
  counts: [{ name: 'level', symbol: 'n', label: 'índice do nível' }],
  notation: null,
  arrays: [
    {
      section: 'observable',
      member: 'matrix',
      label: 'matriz do observável',
      rank: 2,
      presence: 'required',
      is_normalizable: false,
      has_unit: true,
    },
  ],
  settings: [{ name: 'subintervals', label: 'subintervalos da malha uniforme' }],
  requested: null,
  covariance_models: [],
}

describe('describePointer', () => {
  it.each([
    ['/parameters/width/unit', 'grandezas › largura do poço (L) › unidade'],
    ['/parameters/level', 'grandezas › índice do nível (n)'],
    ['/numerics/subintervals', 'resolução numérica › subintervalos da malha uniforme'],
    ['/observable/matrix', 'matriz do observável › matrix'],
    ['/conditions/1', 'condição 2'],
    ['/symbols/y_0/domain', 'símbolos › símbolo y_0 › domínio'],
    ['/requested/significant_digits', 'resposta pedida › algarismos significativos'],
  ])('names %s the way the form does', (pointer, description) => {
    expect(describePointer(pointer, FORM)).toBe(description)
  })

  it('falls back to the section names without a form', () => {
    expect(describePointer('/parameters/width/unit')).toBe('grandezas › width › unidade')
  })

  it('names the whole input for the root pointer', () => {
    expect(describePointer('')).toBe('a entrada inteira')
  })

  it('decodes the escaped characters of a JSON pointer', () => {
    expect(describePointer('/symbols/a~1b')).toBe('símbolos › símbolo a/b')
  })
})
