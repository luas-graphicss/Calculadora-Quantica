import * as v from 'valibot'

const presenceSchema = v.picklist(['required', 'optional'])

const quantityFieldSchema = v.object({
  name: v.string(),
  symbol: v.string(),
  label: v.string(),
  dimension: v.string(),
  units: v.array(v.string()),
  constants: v.array(v.object({ identifier: v.string(), symbol: v.string(), name: v.string() })),
})

const notationFieldsSchema = v.object({
  has_statement: v.boolean(),
  has_equations: v.boolean(),
  has_conditions: v.boolean(),
  has_candidate: v.boolean(),
  symbols_carry_values: v.boolean(),
})

const arrayFieldSchema = v.object({
  section: v.string(),
  member: v.nullable(v.string()),
  label: v.string(),
  rank: v.number(),
  presence: presenceSchema,
  is_normalizable: v.boolean(),
  has_unit: v.boolean(),
})

const requestedFieldsSchema = v.object({
  quantity: v.nullable(v.string()),
  label: v.string(),
  units: v.array(v.string()),
  presence: presenceSchema,
})

const cardFormSchema = v.object({
  kind: v.picklist(['problem', 'statement', 'numerical']),
  confirmations: v.array(v.object({ key: v.string(), value: v.string(), statement: v.string() })),
  quantities: v.array(quantityFieldSchema),
  counts: v.array(v.object({ name: v.string(), symbol: v.string(), label: v.string() })),
  notation: v.nullable(notationFieldsSchema),
  arrays: v.array(arrayFieldSchema),
  settings: v.array(v.object({ name: v.string(), label: v.string() })),
  requested: v.nullable(requestedFieldsSchema),
  covariance_models: v.array(v.string()),
})

const cardSchema = v.object({
  identifier: v.string(),
  version: v.string(),
  title: v.string(),
  domain: v.optional(v.array(v.string()), []),
  method: v.object({ identifier: v.string(), nature: v.string(), justification: v.string() }),
  limitations: v.optional(v.array(v.string()), []),
})

const choiceSchema = v.object({ answer: v.string(), card: cardSchema, form: cardFormSchema })

export const catalogSchema = v.object({
  version: v.string(),
  vocabulary: v.object({
    notations: v.array(v.string()),
    symbol_roles: v.array(v.string()),
    symbol_domains: v.array(v.string()),
  }),
  rounding: v.object({
    default_significant_digits: v.number(),
    max_significant_digits: v.number(),
  }),
  time_limit: v.object({ default_seconds: v.number(), max_seconds: v.number() }),
  questions: v.array(
    v.object({
      identifier: v.string(),
      question: v.string(),
      context: v.string(),
      choices: v.array(choiceSchema),
    }),
  ),
})

export type Catalog = v.InferOutput<typeof catalogSchema>
export type CatalogQuestion = Catalog['questions'][number]
export type CatalogChoice = v.InferOutput<typeof choiceSchema>
export type CardForm = v.InferOutput<typeof cardFormSchema>
export type QuantityField = v.InferOutput<typeof quantityFieldSchema>
export type ArrayField = v.InferOutput<typeof arrayFieldSchema>
export type NotationFields = v.InferOutput<typeof notationFieldsSchema>
export type RequestedFields = v.InferOutput<typeof requestedFieldsSchema>
export type Vocabulary = Catalog['vocabulary']

export function findChoice(catalog: Catalog, cardIdentifier: string) {
  for (const question of catalog.questions) {
    const choice = question.choices.find((item) => item.card.identifier === cardIdentifier)
    if (choice) return { question, choice }
  }
  return undefined
}
