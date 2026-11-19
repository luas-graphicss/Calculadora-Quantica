import * as v from 'valibot'

export const diagnosticSchema = v.object({
  category: v.string(),
  code: v.string(),
  pointer: v.string(),
  message: v.string(),
  expected: v.optional(v.nullable(v.string()), null),
  excerpt: v.optional(
    v.nullable(v.object({ text: v.string(), start: v.number(), end: v.number() })),
    null,
  ),
})

export type Diagnostic = v.InferOutput<typeof diagnosticSchema>

export const rejectionSchema = v.object({
  document: v.literal('rejection'),
  category: v.string(),
  diagnostics: v.array(diagnosticSchema),
})

export type Rejection = v.InferOutput<typeof rejectionSchema>

export const calculationFailureSchema = v.object({
  document: v.literal('calculation_failure'),
  category: v.string(),
  message: v.string(),
})

export const apiErrorSchema = v.object({
  document: v.literal('api_error'),
  code: v.string(),
  message: v.string(),
})
