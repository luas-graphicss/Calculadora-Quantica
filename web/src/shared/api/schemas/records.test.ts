import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

import * as v from 'valibot'
import { describe, expect, it } from 'vitest'

import { rejectionSchema } from '@/shared/api/schemas/diagnostics'
import { runRecordSchema } from '@/shared/api/schemas/records'

const REPOSITORY = path.resolve(import.meta.dirname, '../../../../..')
const EVIDENCE = path.join(REPOSITORY, 'docs/evidence')
const EARLIER_RECORDS = path.join(REPOSITORY, 'tests/fixtures/earlier_records')

function filesEndingWith(directory: string, ending: string): string[] {
  return readdirSync(directory, { recursive: true, encoding: 'utf8' })
    .filter((name) => name.endsWith(ending))
    .map((name) => path.join(directory, name))
    .sort()
}

function documentAt(file: string): unknown {
  return JSON.parse(readFileSync(file, 'utf8'))
}

function nameInRepository(file: string): string {
  return path.relative(REPOSITORY, file)
}

const RECORDED_RUNS = filesEndingWith(EVIDENCE, '.run_record.json').map(nameInRepository)
const RECORDED_REJECTIONS = filesEndingWith(EVIDENCE, '.rejection.json').map(nameInRepository)
const RECORDS_OF_EARLIER_SCHEMAS = filesEndingWith(EARLIER_RECORDS, '.json').map(nameInRepository)

describe('runRecordSchema', () => {
  it('has recorded runs to read', () => {
    expect(RECORDED_RUNS.length).toBeGreaterThan(0)
    expect(RECORDS_OF_EARLIER_SCHEMAS.length).toBeGreaterThan(0)
  })

  it.each(RECORDED_RUNS)('reads the recorded run %s', (file) => {
    const parsed = v.safeParse(runRecordSchema, documentAt(path.join(REPOSITORY, file)))
    expect(parsed.issues).toBeUndefined()
  })

  it.each(RECORDS_OF_EARLIER_SCHEMAS)('reads %s, written with an earlier schema', (file) => {
    const parsed = v.safeParse(runRecordSchema, documentAt(path.join(REPOSITORY, file)))
    expect(parsed.issues).toBeUndefined()
  })
})

describe('rejectionSchema', () => {
  it.each(RECORDED_REJECTIONS)('reads the recorded rejection %s', (file) => {
    const parsed = v.safeParse(rejectionSchema, documentAt(path.join(REPOSITORY, file)))
    expect(parsed.issues).toBeUndefined()
  })
})
