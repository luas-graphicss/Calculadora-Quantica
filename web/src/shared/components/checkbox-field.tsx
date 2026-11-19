import { CircleAlert } from 'lucide-react'
import { useId } from 'react'

type Props = {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  error?: string
}

export function CheckboxField({ label, checked, onChange, error }: Props) {
  const id = useId()
  return (
    <div className="flex flex-col gap-1">
      <div className="flex min-h-11 items-start gap-3 py-1 md:min-h-0">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          aria-invalid={error !== undefined}
          aria-describedby={error === undefined ? undefined : `${id}-error`}
          onChange={(event) => {
            onChange(event.target.checked)
          }}
          className="mt-1 size-4 shrink-0 accent-primary"
        />
        <label htmlFor={id} className="text-sm text-pretty">
          {label}
        </label>
      </div>
      {error === undefined ? null : (
        <p id={`${id}-error`} className="flex items-start gap-1.5 text-sm text-signal">
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
    </div>
  )
}
