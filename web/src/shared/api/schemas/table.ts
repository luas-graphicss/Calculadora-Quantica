import * as v from 'valibot'

const columnSchema = v.object({
  name: v.string(),
  symbol: v.string(),
  unit: v.string(),
  values: v.array(v.number()),
})

export type SampleColumn = v.InferOutput<typeof columnSchema>

export const sampleTableSchema = v.object({
  name: v.string(),
  title: v.string(),
  rows: v.number(),
  columns: v.array(columnSchema),
})

export type SampleTable = v.InferOutput<typeof sampleTableSchema>
