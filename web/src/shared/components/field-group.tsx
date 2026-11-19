import type { ReactNode } from 'react'

type Props = {
  legend: string
  hint?: string
  children: ReactNode
}

export function FieldGroup({ legend, hint, children }: Props) {
  return (
    <fieldset className="flex min-w-0 flex-col gap-4 border-t border-rule pt-5">
      <legend className="float-left w-full text-base font-semibold">{legend}</legend>
      {hint === undefined ? null : <p className="clear-both text-sm text-muted">{hint}</p>}
      <div className="clear-both flex flex-col gap-4">{children}</div>
    </fieldset>
  )
}
