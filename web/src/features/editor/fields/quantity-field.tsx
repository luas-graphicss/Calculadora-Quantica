import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { numberLiteral, optionalText, textAt } from '@/features/editor/input-document'
import type { QuantityField as QuantityDescription } from '@/shared/api/schemas/catalog'
import { SelectField } from '@/shared/components/select-field'
import { TextField } from '@/shared/components/text-field'

type Props = DraftFieldProps & {
  field: QuantityDescription
  section?: readonly string[]
  allowsConstants?: boolean
}

const TYPED_VALUE = ''
const PARAMETERS: readonly string[] = ['parameters']

export function QuantityField({
  field,
  draft,
  onChange,
  section = PARAMETERS,
  allowsConstants = true,
}: Props) {
  const path = [...section, field.name]
  const constant = textAt(draft, [...path, 'constant'])
  const groupError = useFieldError(pointerOf(path))
  const valueError = useFieldError(pointerOf([...path, 'value']))
  const unitError = useFieldError(pointerOf([...path, 'unit']))
  const constantError = useFieldError(pointerOf([...path, 'constant']))
  const name = `${field.label} (${field.symbol})`
  const constants = allowsConstants ? field.constants : []

  return (
    <div role="group" aria-label={name} className="flex flex-col gap-2">
      <p className="text-sm font-medium">
        {field.label} <span className="font-mono text-muted">{`(${field.symbol})`}</span>
      </p>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {constants.length === 0 ? null : (
          <SelectField
            label={`Origem de ${field.symbol}`}
            value={constant}
            error={constantError}
            options={[
              { value: TYPED_VALUE, label: 'valor informado' },
              ...constants.map((choice) => ({
                value: choice.identifier,
                label: `${choice.name} (${choice.symbol}), constante do catálogo`,
              })),
            ]}
            onChange={(chosen) => {
              onChange(path, chosen === TYPED_VALUE ? undefined : { constant: chosen })
            }}
          />
        )}
        {constant !== '' ? null : (
          <>
            <TextField
              label={`Valor de ${field.symbol}`}
              value={textAt(draft, [...path, 'value'])}
              inputMode="decimal"
              monospace
              error={valueError ?? groupError}
              onChange={(text) => {
                onChange([...path, 'value'], numberLiteral(text))
              }}
            />
            <SelectField
              label={`Unidade de ${field.symbol}`}
              value={textAt(draft, [...path, 'unit'])}
              placeholder={`escolha (${field.dimension})`}
              error={unitError}
              options={field.units.map((unit) => ({ value: unit, label: unit }))}
              onChange={(unit) => {
                onChange([...path, 'unit'], optionalText(unit))
              }}
            />
          </>
        )}
      </div>
    </div>
  )
}
