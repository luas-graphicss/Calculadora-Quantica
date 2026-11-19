import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { numberLiteral, optionalText, textAt } from '@/features/editor/input-document'
import type { Catalog, RequestedFields as RequestedDescription } from '@/shared/api/schemas/catalog'
import { FieldGroup } from '@/shared/components/field-group'
import { SelectField } from '@/shared/components/select-field'
import { TextField } from '@/shared/components/text-field'

type Props = DraftFieldProps & {
  requested: RequestedDescription
  rounding: Catalog['rounding']
}

export function RequestedFields({ requested, rounding, draft, onChange }: Props) {
  const unitError = useFieldError(pointerOf(['requested', 'unit']))
  const digitsError = useFieldError(pointerOf(['requested', 'significant_digits']))
  const sectionError = useFieldError('/requested')
  const unitLabel =
    requested.quantity === null ? 'Unidade das respostas' : `Unidade de ${requested.label}`

  return (
    <FieldGroup legend="Resposta pedida">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {requested.units.length === 0 ? null : (
          <SelectField
            label={unitLabel}
            value={textAt(draft, ['requested', 'unit'])}
            placeholder="escolha"
            error={unitError ?? sectionError}
            options={requested.units.map((unit) => ({ value: unit, label: unit }))}
            onChange={(unit) => {
              onChange(['requested', 'unit'], optionalText(unit))
            }}
          />
        )}
        <TextField
          label="Algarismos significativos"
          value={textAt(draft, ['requested', 'significant_digits'])}
          inputMode="numeric"
          monospace
          hint={`Em branco: ${rounding.default_significant_digits}. Máximo: ${rounding.max_significant_digits}.`}
          error={digitsError}
          onChange={(text) => {
            onChange(['requested', 'significant_digits'], numberLiteral(text))
          }}
        />
      </div>
    </FieldGroup>
  )
}
