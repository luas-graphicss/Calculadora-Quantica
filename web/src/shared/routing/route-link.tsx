import type { ReactNode } from 'react'

import { formatRoute, type Route } from '@/shared/routing/routes'

type Props = {
  to: Route
  className?: string
  current?: boolean
  children: ReactNode
}

export function RouteLink({ to, className, current = false, children }: Props) {
  return (
    <a href={formatRoute(to)} className={className} aria-current={current ? 'page' : undefined}>
      {children}
    </a>
  )
}
