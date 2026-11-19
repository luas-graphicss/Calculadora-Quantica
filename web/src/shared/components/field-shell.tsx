import { CircleAlert } from 'lucide-react'
import type { ReactNode } from 'react'

type Props = {
  id: string
  label: string
  hint?: string
  error?: string
  children: ReactNode
}

export function fieldDescription(id: string, hint?: string, error?: string): string | undefined {
  const described = [
    hint === undefined ? null : `${id}-hint`,
    error === undefined ? null : `${id}-error`,
  ].filter((item) => item !== null)
  return described.length === 0 ? undefined : described.join(' ')
}

export function FieldShell({ id, label, hint, error, children }: Props) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      {children}
      {hint === undefined ? null : (
        <p id={`${id}-hint`} className="text-sm text-muted">
          {hint}
        </p>
      )}
      {error === undefined ? null : (
        <p id={`${id}-error`} className="flex items-start gap-1.5 text-sm text-signal">
          <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}
    </div>
  )
}
