import { ArrayField } from '@/features/editor/fields/array-field'
import { ConfirmationList } from '@/features/editor/fields/confirmation-list'
import { CountField } from '@/features/editor/fields/count-field'
import type { DraftFieldProps } from '@/features/editor/fields/draft-field'
import { NotationFields } from '@/features/editor/fields/notation-fields'
import { QuantityField } from '@/features/editor/fields/quantity-field'
import { RequestedFields } from '@/features/editor/fields/requested-fields'
import { SettingFields } from '@/features/editor/fields/setting-fields'
import { UncertaintyFields } from '@/features/editor/fields/uncertainty-fields'
import { optionalText, textAt } from '@/features/editor/input-document'
import type { CardForm, Catalog } from '@/shared/api/schemas/catalog'
import { FieldGroup } from '@/shared/components/field-group'
import { TextField } from '@/shared/components/text-field'

type Props = DraftFieldProps & {
  form: CardForm
  catalog: Catalog
  revision: number
}

export function CardFormFields({ form, catalog, revision, draft, onChange }: Props) {
  return (
    <div className="flex flex-col gap-8">
      {form.confirmations.length === 0 ? null : (
        <ConfirmationList confirmations={form.confirmations} draft={draft} onChange={onChange} />
      )}
      {form.quantities.length + form.counts.length === 0 ? null : (
        <FieldGroup legend="Grandezas">
          {form.quantities.map((field) => (
            <QuantityField key={field.name} field={field} draft={draft} onChange={onChange} />
          ))}
          {form.counts.map((field) => (
            <CountField key={field.name} field={field} draft={draft} onChange={onChange} />
          ))}
        </FieldGroup>
      )}
      {form.notation === null ? null : (
        <NotationFields
          key={revision}
          notation={form.notation}
          vocabulary={catalog.vocabulary}
          draft={draft}
          onChange={onChange}
        />
      )}
      {form.arrays.length === 0 ? null : (
        <FieldGroup legend="Estados e operadores">
          {form.arrays.map((field) => (
            <ArrayField
              key={`${revision}:${field.section}`}
              field={field}
              draft={draft}
              onChange={onChange}
            />
          ))}
        </FieldGroup>
      )}
      {form.settings.length === 0 ? null : (
        <SettingFields settings={form.settings} draft={draft} onChange={onChange} />
      )}
      {form.requested === null ? null : (
        <RequestedFields
          requested={form.requested}
          rounding={catalog.rounding}
          draft={draft}
          onChange={onChange}
        />
      )}
      {form.covariance_models.length === 0 ? null : (
        <UncertaintyFields
          models={form.covariance_models}
          quantities={form.quantities}
          draft={draft}
          onChange={onChange}
        />
      )}
      <FieldGroup legend="Anotação">
        <TextField
          label="Descrição do problema (opcional)"
          value={textAt(draft, ['description'])}
          hint="Fica guardada com a execução, para você reconhecer o cálculo no histórico."
          onChange={(text) => {
            onChange(['description'], optionalText(text))
          }}
        />
      </FieldGroup>
    </div>
  )
}
