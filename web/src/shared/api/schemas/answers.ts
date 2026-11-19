import * as v from 'valibot'

const displayedAnswerSchema = v.object({
  name: v.string(),
  symbol: v.string(),
  label: v.string(),
  value: v.string(),
  unit: v.string(),
  error: v.nullable(v.string()),
  error_origin: v.nullable(v.string()),
})

export type DisplayedAnswer = v.InferOutput<typeof displayedAnswerSchema>

export const answersSchema = v.object({
  run_identifier: v.string(),
  display_units: v.array(v.string()),
  answers: v.array(displayedAnswerSchema),
})

export type Answers = v.InferOutput<typeof answersSchema>
