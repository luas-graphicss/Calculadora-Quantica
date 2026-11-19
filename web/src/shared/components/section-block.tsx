import { type ReactNode, useId } from 'react'

type Props = {
  title: string
  children: ReactNode
}

export function SectionBlock({ title, children }: Props) {
  const headingId = useId()
  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-4 border-t border-rule pt-6">
      <h2 id={headingId} className="text-lg font-semibold">
        {title}
      </h2>
      {children}
    </section>
  )
}
