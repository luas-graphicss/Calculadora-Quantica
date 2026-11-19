import { describe, expect, it } from 'vitest'

import {
  draftCard,
  numberLiteral,
  optionalText,
  parseDraft,
  readPath,
  serializeDraft,
  textAt,
  writePath,
} from '@/features/editor/input-document'

describe('writePath', () => {
  it('creates the sections on the way to a new field', () => {
    expect(writePath({}, ['parameters', 'width', 'value'], 1)).toEqual({
      parameters: { width: { value: 1 } },
    })
  })

  it('removes a section when its last field is cleared', () => {
    const draft = { problem: 'card', parameters: { width: { value: 1 } } }
    expect(writePath(draft, ['parameters', 'width', 'value'], undefined)).toEqual({
      problem: 'card',
    })
  })

  it('keeps the place of a field that already exists', () => {
    expect(Object.keys(writePath({ a: 1, b: 2, c: 3 }, ['b'], 20))).toEqual(['a', 'b', 'c'])
  })

  it('does not change the draft it receives', () => {
    const draft = { parameters: { width: { value: 1 } } }
    writePath(draft, ['parameters', 'width', 'value'], 2)
    expect(draft).toEqual({ parameters: { width: { value: 1 } } })
  })

  it('refuses keys that would reach the object prototype', () => {
    const draft = { problem: 'card' }
    const untouched: Record<string, unknown> = {}

    expect(writePath(draft, ['__proto__', 'polluted'], true)).toBe(draft)
    expect(writePath(draft, ['parameters', 'constructor'], true)).toEqual(draft)
    expect(untouched.polluted).toBeUndefined()
  })
})

describe('readPath', () => {
  it('reads only the fields the draft owns', () => {
    const draft = { parameters: { width: { value: 1 } } }
    expect(readPath(draft, ['parameters', 'width', 'value'])).toBe(1)
    expect(readPath(draft, ['parameters', 'mass'])).toBeUndefined()
    expect(readPath(draft, ['toString'])).toBeUndefined()
  })
})

describe('textAt', () => {
  it('shows numbers and text, and nothing for any other value', () => {
    const draft = { level: 1, unit: 'nm', normalize: true }
    expect(textAt(draft, ['level'])).toBe('1')
    expect(textAt(draft, ['unit'])).toBe('nm')
    expect(textAt(draft, ['normalize'])).toBe('')
    expect(textAt(draft, ['absent'])).toBe('')
  })
})

describe('numberLiteral', () => {
  it('keeps as text whatever a double could round', () => {
    expect(numberLiteral('3')).toBe(3)
    expect(numberLiteral(' -12 ')).toBe(-12)
    expect(numberLiteral('3.666077985')).toBe('3.666077985')
    expect(numberLiteral('1e-9')).toBe('1e-9')
    expect(numberLiteral('1234567890123456')).toBe('1234567890123456')
  })

  it('treats a blank field as absent', () => {
    expect(numberLiteral('   ')).toBeUndefined()
  })
})

describe('optionalText', () => {
  it('treats a blank field as absent and keeps the rest as typed', () => {
    expect(optionalText('  ')).toBeUndefined()
    expect(optionalText(" y' = -k*y ")).toBe(" y' = -k*y ")
  })
})

describe('serializeDraft', () => {
  it('writes the sections in the order of the input schema, whatever the editing order', () => {
    const draft = {
      requested: { unit: 'eV' },
      zeta: 1,
      problem: 'card',
      alpha: 2,
      schema_version: '1.0',
    }
    const written: unknown = JSON.parse(serializeDraft(draft))

    expect(Object.keys(written as object)).toEqual([
      'schema_version',
      'problem',
      'requested',
      'alpha',
      'zeta',
    ])
  })

  it('ends with a line break', () => {
    expect(serializeDraft({})).toBe('{}\n')
  })
})

describe('parseDraft', () => {
  it('accepts a JSON object', () => {
    expect(parseDraft('{"problem": "card"}')).toEqual({ ok: true, draft: { problem: 'card' } })
  })

  it.each(['[1, 2]', '"text"', 'null', '3'])('refuses %s, which is not an object', (text) => {
    expect(parseDraft(text)).toEqual({
      ok: false,
      message: 'A entrada precisa ser um objeto JSON, entre chaves.',
    })
  })

  it('explains text that is not JSON', () => {
    const parsed = parseDraft('{"problem": ')
    expect(parsed.ok ? '' : parsed.message).toContain('O texto não é JSON válido')
  })
})

describe('draftCard', () => {
  it('reads the card only when it is text', () => {
    expect(draftCard({ problem: 'calculus.derivative' })).toBe('calculus.derivative')
    expect(draftCard({ problem: 3 })).toBeNull()
    expect(draftCard({})).toBeNull()
  })
})
