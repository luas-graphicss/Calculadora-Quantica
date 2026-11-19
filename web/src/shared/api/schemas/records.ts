import * as v from 'valibot'

const expressionSchema = v.object({ text: v.string(), latex: v.string() })

export type NotatedExpression = v.InferOutput<typeof expressionSchema>

const quantityValueSchema = v.object({ decimal: v.string(), unit: v.string() })

const roundingSchema = v.object({ mode: v.string(), significant_digits: v.number() })

const labeledValueSchema = v.object({
  name: v.string(),
  label: v.string(),
  value: v.string(),
  origin: v.optional(v.string()),
})

export type LabeledValue = v.InferOutput<typeof labeledValueSchema>

const hypothesisSchema = v.object({ key: v.string(), value: v.string(), statement: v.string() })

const parameterSchema = v.object({
  name: v.string(),
  symbol: v.string(),
  origin: v.string(),
  constant: v.optional(v.string()),
  given: v.optional(v.object({ value: v.string(), unit: v.string() })),
  si: v.optional(quantityValueSchema),
  count: v.optional(v.string()),
})

const declaredUncertaintySchema = v.object({
  covariance: v.string(),
  standard_uncertainties: v.array(
    v.object({ parameter: v.string(), given: v.object({ value: v.string(), unit: v.string() }) }),
  ),
})

const problemSchema = v.object({
  card: v.object({ identifier: v.string(), version: v.string(), title: v.string() }),
  scope: v.optional(v.array(v.string()), []),
  domain: v.optional(v.array(v.string()), []),
  hypotheses: v.optional(v.array(hypothesisSchema), []),
  parameters: v.optional(v.array(parameterSchema), []),
  requested: v.optional(
    v.object({
      symbol: v.string(),
      label: v.string(),
      unit: v.string(),
      significant_digits: v.number(),
    }),
  ),
  uncertainty: v.optional(v.nullable(declaredUncertaintySchema), null),
  notation: v.optional(v.string()),
  statement: v.optional(v.nullable(expressionSchema), null),
  symbols: v.optional(
    v.array(
      v.object({
        name: v.string(),
        role: v.string(),
        domain: v.string(),
        unit: v.string(),
        argument: v.optional(v.nullable(v.string()), null),
      }),
    ),
    [],
  ),
  conditions: v.optional(v.array(expressionSchema), []),
  candidate: v.optional(v.nullable(expressionSchema), null),
  result_unit: v.optional(v.string()),
  inputs: v.optional(v.array(labeledValueSchema), []),
  resolution: v.optional(v.array(labeledValueSchema), []),
  estimate: v.optional(v.object({ memory_bytes: v.number(), operations: v.number() })),
  rounding: v.optional(roundingSchema),
})

export type ProblemSection = v.InferOutput<typeof problemSchema>

const planSchema = v.object({
  method: v.string(),
  nature: v.string(),
  justification: v.string(),
  rounding: v.optional(roundingSchema),
  budget: v.optional(v.object({ wall_seconds: v.number() })),
})

export type PlanSection = v.InferOutput<typeof planSchema>

export const interpretationSchema = v.object({
  document: v.picklist(['validation', 'statement_validation', 'numerical_validation']),
  schema_version: v.string(),
  problem: problemSchema,
  plan: planSchema,
})

export type Interpretation = v.InferOutput<typeof interpretationSchema>

const describedConditionSchema = v.object({ text: v.string() })

const specialCaseSchema = v.object({ when: expressionSchema, answer: expressionSchema })

const stepSchema = v.object({
  description: v.string(),
  expression: v.union([v.string(), expressionSchema]),
  value: v.optional(v.nullable(quantityValueSchema), null),
})

export type CalculationStep = v.InferOutput<typeof stepSchema>

const propagatedUncertaintySchema = v.object({
  status: v.string(),
  reason: v.optional(v.string()),
  covariance: v.optional(v.string()),
  standard_uncertainty: v.optional(quantityValueSchema),
  relative_standard_uncertainty: v.optional(v.string()),
  contributions: v.optional(
    v.array(
      v.object({
        parameter: v.string(),
        symbol: v.string(),
        sensitivity: quantityValueSchema,
        standard_uncertainty: quantityValueSchema,
      }),
    ),
    [],
  ),
})

const tableOutlineSchema = v.object({
  name: v.string(),
  title: v.string(),
  rows: v.number(),
  columns: v.array(v.object({ name: v.string(), symbol: v.string(), unit: v.string() })),
})

export type TableOutline = v.InferOutput<typeof tableOutlineSchema>

const resultSchema = v.object({
  nature: v.string(),
  expression: v.optional(v.object({ plain: v.string(), latex: v.string() })),
  si_value: v.optional(quantityValueSchema),
  uncertainty: v.optional(propagatedUncertaintySchema),
  answer: v.optional(expressionSchema),
  unit: v.optional(v.string()),
  validity: v.optional(v.array(describedConditionSchema), []),
  assumptions: v.optional(v.array(describedConditionSchema), []),
  special_cases: v.optional(v.array(specialCaseSchema), []),
  arbitrary_constants: v.optional(v.array(v.string()), []),
  certificate: v.optional(v.nullable(expressionSchema), null),
  steps: v.optional(v.array(stepSchema), []),
  tables: v.optional(v.array(tableOutlineSchema), []),
  effective: v.optional(v.array(labeledValueSchema), []),
  warnings: v.optional(v.array(v.string()), []),
})

export type ResultSection = v.InferOutput<typeof resultSchema>

const verificationSchema = v.object({
  status: v.string(),
  checks: v.array(
    v.object({
      identifier: v.string(),
      kind: v.string(),
      status: v.string(),
      statement: v.string(),
      observed: v.optional(v.nullable(v.string()), null),
    }),
  ),
  not_performed: v.optional(v.array(v.object({ identifier: v.string(), reason: v.string() })), []),
  references: v.optional(v.array(v.string()), []),
})

export type VerificationSection = v.InferOutput<typeof verificationSchema>

const constantsSchema = v.object({
  edition: v.string(),
  used: v.optional(
    v.array(
      v.object({
        identifier: v.string(),
        symbol: v.string(),
        name: v.string(),
        value: quantityValueSchema,
        exactness: v.string(),
        source: v.optional(v.nullable(v.string()), null),
      }),
    ),
    [],
  ),
})

export type ConstantsSection = v.InferOutput<typeof constantsSchema>

const environmentSchema = v.object({
  package: v.object({ name: v.string(), version: v.string() }),
  python: v.object({ implementation: v.string(), version: v.string() }),
  platform: v.string(),
  dependencies: v.optional(v.array(v.object({ name: v.string(), version: v.string() })), []),
  linear_algebra: v.optional(
    v.array(
      v.object({
        consumer: v.string(),
        interface: v.string(),
        name: v.string(),
        version: v.string(),
      }),
    ),
    [],
  ),
})

export type EnvironmentSection = v.InferOutput<typeof environmentSchema>

export const runRecordSchema = v.object({
  document: v.picklist(['run_record', 'statement_run_record', 'numerical_run_record']),
  schema_version: v.string(),
  problem: problemSchema,
  plan: planSchema,
  result: resultSchema,
  verification: verificationSchema,
  limitations: v.optional(v.array(v.string()), []),
  constants: v.optional(constantsSchema),
  catalog: v.optional(v.object({ version: v.string() })),
  units: v.optional(v.object({ registry_version: v.string() })),
  environment: v.optional(environmentSchema),
})

export type RunRecord = v.InferOutput<typeof runRecordSchema>
