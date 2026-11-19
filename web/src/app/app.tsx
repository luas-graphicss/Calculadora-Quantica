import { useEffect, useRef } from 'react'

import { RouteView } from '@/app/route-view'
import { SessionRequired } from '@/app/session-required'
import { SiteHeader } from '@/app/site-header'
import { useSession } from '@/shared/api/queries'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { formatRoute } from '@/shared/routing/routes'
import { useRoute } from '@/shared/routing/use-route'

const SKIP_LINK =
  'sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-10 focus:rounded-md ' +
  'focus:border focus:border-ink focus:bg-surface focus:px-4 focus:py-2 focus:text-sm'

export function App() {
  const route = useRoute()
  const session = useSession()
  const main = useRef<HTMLElement>(null)
  const location = formatRoute(route)
  const shownLocation = useRef(location)

  useEffect(() => {
    if (shownLocation.current === location) return
    shownLocation.current = location
    main.current?.focus()
    window.scrollTo({ top: 0 })
  }, [location])

  return (
    <div className="flex min-h-dvh flex-col">
      <button
        type="button"
        onClick={() => {
          main.current?.focus()
        }}
        className={SKIP_LINK}
      >
        Ir para o conteúdo
      </button>
      <SiteHeader route={route} />
      <main
        ref={main}
        tabIndex={-1}
        className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 focus:outline-none md:px-8 md:py-10"
      >
        {session.error === undefined ? null : <ErrorNotice error={session.error} />}
        {session.data === undefined && session.error === undefined ? (
          <LoadingLine label="Abrindo a bancada" />
        ) : null}
        {session.data === false ? <SessionRequired /> : null}
        {session.data === true ? <RouteView route={route} /> : null}
      </main>
      <footer className="border-t border-rule">
        <p className="mx-auto w-full max-w-5xl px-4 py-4 text-sm text-muted md:px-8">
          Os cálculos, o histórico e os pacotes ficam nesta máquina.
        </p>
      </footer>
    </div>
  )
}
