import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { numberLiteral, textAt } from '@/features/editor/input-document'
import type { CardForm } from '@/shared/api/schemas/catalog'
import { FieldGroup } from '@/shared/components/field-group'
import { TextField } from '@/shared/components/text-field'

type Setting = CardForm['settings'][number]

type ItemProps = DraftFieldProps & {
  setting: Setting
}

function capitalized(label: string): string {
  return label.charAt(0).toUpperCase() + label.slice(1)
}

function SettingItem({ setting, draft, onChange }: ItemProps) {
  const path = ['numerics', setting.name]
  const error = useFieldError(pointerOf(path))
  return (
    <TextField
      label={capitalized(setting.label)}
      value={textAt(draft, path)}
      inputMode="decimal"
      monospace
      error={error}
      onChange={(text) => {
        onChange(path, numberLiteral(text))
      }}
    />
  )
}

type Props = DraftFieldProps & {
  settings: readonly Setting[]
}

export function SettingFields({ settings, draft, onChange }: Props) {
  const error = useFieldError('/numerics')
  return (
    <FieldGroup
      legend="Resolução numérica"
      hint="Estes valores definem a aproximação. A calculadora não escolhe nenhum por você."
    >
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {settings.map((setting) => (
          <SettingItem key={setting.name} setting={setting} draft={draft} onChange={onChange} />
        ))}
      </div>
      {error === undefined ? null : <p className="text-sm text-signal">{error}</p>}
    </FieldGroup>
  )
}
