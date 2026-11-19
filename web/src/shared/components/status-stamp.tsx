import type { StatusDescription, Tone } from '@/shared/format/labels'

type Props = {
  status: StatusDescription
  prefix?: string
}

const TONES = {
  positive: 'border-primary text-primary',
  neutral: 'border-ink text-ink',
  negative: 'border-signal text-signal',
} as const satisfies Record<Tone, string>

export function StatusStamp({ status, prefix }: Props) {
  const Icon = status.icon
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-semibold tracking-wide whitespace-nowrap uppercase ${TONES[status.tone]}`}
    >
      <Icon className="size-3.5" aria-hidden="true" strokeWidth={2} />
      {prefix === undefined ? status.label : `${prefix} ${status.label}`}
    </span>
  )
}
