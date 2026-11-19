import { useId } from 'react'

import { inputControl } from '@/shared/components/button-styles'
import { fieldDescription, FieldShell } from '@/shared/components/field-shell'

export type SelectOption = {
  value: string
  label: string
}

type Props = {
  label: string
  value: string
  options: readonly SelectOption[]
  onChange: (value: string) => void
  placeholder?: string
  hint?: string
  error?: string
}

export function SelectField({ label, value, options, onChange, placeholder, hint, error }: Props) {
  const id = useId()
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <select
        id={id}
        value={value}
        aria-invalid={error !== undefined}
        aria-describedby={fieldDescription(id, hint, error)}
        onChange={(event) => {
          onChange(event.target.value)
        }}
        className={inputControl}
      >
        {placeholder === undefined ? null : <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </FieldShell>
  )
}
