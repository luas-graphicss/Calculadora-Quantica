import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { numberLiteral, textAt } from '@/features/editor/input-document'
import type { CardForm } from '@/shared/api/schemas/catalog'
import { TextField } from '@/shared/components/text-field'

type Props = DraftFieldProps & {
  field: CardForm['counts'][number]
}

export function CountField({ field, draft, onChange }: Props) {
  const path = ['parameters', field.name]
  const error = useFieldError(pointerOf(path))
  return (
    <div className="grid grid-cols-1 md:grid-cols-3">
      <TextField
        label={`${field.label} (${field.symbol})`}
        value={textAt(draft, path)}
        inputMode="numeric"
        monospace
        error={error}
        onChange={(text) => {
          onChange(path, numberLiteral(text))
        }}
      />
    </div>
  )
}
