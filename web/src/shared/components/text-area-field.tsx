import { useId } from 'react'

import { inputControl } from '@/shared/components/button-styles'
import { fieldDescription, FieldShell } from '@/shared/components/field-shell'

type Props = {
  label: string
  value: string
  onChange: (value: string) => void
  rows: number
  hint?: string
  error?: string
}

export function TextAreaField({ label, value, onChange, rows, hint, error }: Props) {
  const id = useId()
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <textarea
        id={id}
        value={value}
        rows={rows}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        aria-invalid={error !== undefined}
        aria-describedby={fieldDescription(id, hint, error)}
        onChange={(event) => {
          onChange(event.target.value)
        }}
        className={`${inputControl} font-mono`}
      />
    </FieldShell>
  )
}
