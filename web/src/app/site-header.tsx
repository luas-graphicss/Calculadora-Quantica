import { BrandMark } from '@/app/brand-mark'
import { RouteLink } from '@/shared/routing/route-link'
import type { Route } from '@/shared/routing/routes'

type Props = {
  route: Route
}

const NAVIGATION_LINK =
  'inline-flex min-h-11 items-center px-3 text-sm decoration-2 underline-offset-8 hover:underline ' +
  'aria-[current=page]:font-semibold aria-[current=page]:underline md:min-h-9'

export function SiteHeader({ route }: Props) {
  const isFormulating = route.name === 'catalog' || route.name === 'editor'
  const isReviewing =
    route.name === 'history' || route.name === 'run' || route.name === 'comparison'

  return (
    <header className="border-b border-rule bg-surface">
      <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-6 px-4 py-2 md:px-8">
        <RouteLink
          to={{ name: 'catalog' }}
          className="flex min-h-11 items-center gap-2 font-semibold md:min-h-9"
        >
          <BrandMark />
          Calculadora Quântica
        </RouteLink>
        <nav aria-label="Seções">
          <ul className="flex">
            <li>
              <RouteLink
                to={{ name: 'catalog' }}
                current={isFormulating}
                className={NAVIGATION_LINK}
              >
                Problemas
              </RouteLink>
            </li>
            <li>
              <RouteLink to={{ name: 'history' }} current={isReviewing} className={NAVIGATION_LINK}>
                Histórico
              </RouteLink>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  )
}
