import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { readPath } from '@/features/editor/input-document'
import type { CardForm } from '@/shared/api/schemas/catalog'
import { CheckboxField } from '@/shared/components/checkbox-field'
import { FieldGroup } from '@/shared/components/field-group'

type Confirmation = CardForm['confirmations'][number]

type ItemProps = DraftFieldProps & {
  confirmation: Confirmation
}

function ConfirmationItem({ confirmation, draft, onChange }: ItemProps) {
  const path = ['hypotheses', confirmation.key]
  const error = useFieldError(pointerOf(path))
  return (
    <CheckboxField
      label={confirmation.statement}
      checked={readPath(draft, path) === confirmation.value}
      error={error}
      onChange={(checked) => {
        onChange(path, checked ? confirmation.value : undefined)
      }}
    />
  )
}

type Props = DraftFieldProps & {
  confirmations: readonly Confirmation[]
}

export function ConfirmationList({ confirmations, draft, onChange }: Props) {
  const error = useFieldError('/hypotheses')
  return (
    <FieldGroup
      legend="Hipóteses do modelo"
      hint="Marque as que valem para o seu problema. A ficha só calcula com todas confirmadas."
    >
      {confirmations.map((confirmation) => (
        <ConfirmationItem
          key={confirmation.key}
          confirmation={confirmation}
          draft={draft}
          onChange={onChange}
        />
      ))}
      {error === undefined ? null : <p className="text-sm text-signal">{error}</p>}
    </FieldGroup>
  )
}
