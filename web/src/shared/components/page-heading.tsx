import type { ReactNode } from 'react'

type Props = {
  title: string
  eyebrow?: string
  children?: ReactNode
}

export function PageHeading({ title, eyebrow, children }: Props) {
  return (
    <header className="flex flex-col gap-2 border-b border-ink pb-5">
      {eyebrow === undefined ? null : <p className="text-sm text-muted">{eyebrow}</p>}
      <h1 className="text-2xl leading-tight font-semibold tracking-tight text-balance md:text-3xl">
        {title}
      </h1>
      {children}
    </header>
  )
}
