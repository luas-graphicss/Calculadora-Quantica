import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { QuantityField } from '@/features/editor/fields/quantity-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { textAt } from '@/features/editor/input-document'
import type { QuantityField as QuantityDescription } from '@/shared/api/schemas/catalog'
import { FieldGroup } from '@/shared/components/field-group'
import { SelectField } from '@/shared/components/select-field'
import { describeTerm } from '@/shared/format/labels'

type Props = DraftFieldProps & {
  models: readonly string[]
  quantities: readonly QuantityDescription[]
}

const NOT_PROPAGATED = ''
const UNCERTAINTIES: readonly string[] = ['uncertainty', 'standard_uncertainties']

export function UncertaintyFields({ models, quantities, draft, onChange }: Props) {
  const covariance = textAt(draft, ['uncertainty', 'covariance'])
  const error = useFieldError(pointerOf(['uncertainty', 'covariance']))
  const sectionError = useFieldError('/uncertainty')

  return (
    <FieldGroup
      legend="Incerteza dos dados"
      hint="Opcional. Sem declaração, o resultado sai com incerteza não avaliada, e não com zero."
    >
      <div className="grid grid-cols-1 md:grid-cols-3">
        <SelectField
          label="Covariância entre os dados"
          value={covariance}
          error={error ?? sectionError}
          options={[
            { value: NOT_PROPAGATED, label: 'não propagar incerteza' },
            ...models.map((model) => ({ value: model, label: describeTerm(model) })),
          ]}
          onChange={(model) => {
            onChange(['uncertainty'], model === NOT_PROPAGATED ? undefined : { covariance: model })
          }}
        />
      </div>
      {covariance === NOT_PROPAGATED
        ? null
        : quantities.map((quantity) => (
            <QuantityField
              key={quantity.name}
              field={{ ...quantity, label: `incerteza padrão de ${quantity.label}` }}
              section={UNCERTAINTIES}
              allowsConstants={false}
              draft={draft}
              onChange={onChange}
            />
          ))}
    </FieldGroup>
  )
}
