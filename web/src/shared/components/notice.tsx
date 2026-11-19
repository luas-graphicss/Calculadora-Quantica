import { CircleAlert, Info } from 'lucide-react'
import type { ReactNode } from 'react'

type Props = {
  tone: 'information' | 'problem'
  title?: string
  children: ReactNode
}

export function Notice({ tone, title, children }: Props) {
  const isProblem = tone === 'problem'
  const Icon = isProblem ? CircleAlert : Info
  return (
    <div
      role={isProblem ? 'alert' : 'status'}
      className={`flex items-start gap-3 rounded-md border bg-surface px-4 py-3 text-sm ${
        isProblem ? 'border-signal' : 'border-rule-strong'
      }`}
    >
      <Icon
        className={`mt-0.5 size-4 shrink-0 ${isProblem ? 'text-signal' : 'text-muted'}`}
        aria-hidden="true"
      />
      <div className="flex min-w-0 flex-col gap-1">
        {title === undefined ? null : <p className="font-semibold">{title}</p>}
        <div className="text-pretty">{children}</div>
      </div>
    </div>
  )
}
