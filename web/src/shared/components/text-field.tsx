import { useId } from 'react'

import { inputControl } from '@/shared/components/button-styles'
import { fieldDescription, FieldShell } from '@/shared/components/field-shell'

type Props = {
  label: string
  value: string
  onChange: (value: string) => void
  hint?: string
  error?: string
  inputMode?: 'text' | 'decimal' | 'numeric'
  monospace?: boolean
  disabled?: boolean
}

export function TextField({
  label,
  value,
  onChange,
  hint,
  error,
  inputMode = 'text',
  monospace = false,
  disabled = false,
}: Props) {
  const id = useId()
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <input
        id={id}
        type="text"
        value={value}
        inputMode={inputMode}
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        disabled={disabled}
        aria-invalid={error !== undefined}
        aria-describedby={fieldDescription(id, hint, error)}
        onChange={(event) => {
          onChange(event.target.value)
        }}
        className={monospace ? `${inputControl} font-mono` : inputControl}
      />
    </FieldShell>
  )
}
