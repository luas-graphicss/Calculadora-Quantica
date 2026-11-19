import * as v from 'valibot'

import { runSchema } from '@/shared/api/schemas/run'

const comparedValueSchema = v.nullable(v.object({ value: v.string(), unit: v.string() }))

const sideBySideSchema = v.object({
  base: v.nullable(v.string()),
  other: v.nullable(v.string()),
})

export const comparisonSchema = v.object({
  base: runSchema,
  other: runSchema,
  version_divergences: v.array(v.object({ subject: v.string(), ...sideBySideSchema.entries })),
  input_differences: v.array(v.object({ pointer: v.string(), ...sideBySideSchema.entries })),
  method: sideBySideSchema,
  answers: v.array(
    v.object({
      name: v.string(),
      symbol: v.string(),
      label: v.string(),
      base: comparedValueSchema,
      other: comparedValueSchema,
      ratio: v.nullable(v.string()),
    }),
  ),
})

export type Comparison = v.InferOutput<typeof comparisonSchema>
