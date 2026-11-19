import { useSyncExternalStore } from 'react'

import { formatRoute, parseRoute, type Route } from '@/shared/routing/routes'

function subscribe(notify: () => void): () => void {
  window.addEventListener('hashchange', notify)
  return () => {
    window.removeEventListener('hashchange', notify)
  }
}

function currentHash(): string {
  return window.location.hash
}

export function useRoute(): Route {
  return parseRoute(useSyncExternalStore(subscribe, currentHash))
}

export function navigate(route: Route): void {
  window.location.hash = formatRoute(route)
}
