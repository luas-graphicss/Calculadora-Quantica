import useSWR from 'swr'

import {
  fetchAnswers,
  fetchCatalog,
  fetchComparison,
  fetchRunDetails,
  fetchRuns,
  fetchTable,
  hasSession,
} from '@/shared/api/client'
import { isActive } from '@/shared/api/schemas/run'

const ACTIVE_RUN_POLL_MS = 1_000
const ACTIVE_HISTORY_POLL_MS = 2_000
const STABLE = { revalidateOnFocus: false, revalidateIfStale: false } as const

export const RUNS_KEY = 'runs'

export function runKey(identifier: string) {
  return ['run', identifier] as const
}

export function useSession() {
  return useSWR('session', hasSession, { revalidateOnFocus: true })
}

export function useCatalog() {
  return useSWR('catalog', fetchCatalog, STABLE)
}

export function useRuns() {
  return useSWR(RUNS_KEY, fetchRuns, {
    refreshInterval: (runs) => (runs?.some(isActive) ? ACTIVE_HISTORY_POLL_MS : 0),
  })
}

export function useRunDetails(identifier: string) {
  return useSWR(runKey(identifier), () => fetchRunDetails(identifier), {
    refreshInterval: (details) => (details && isActive(details.run) ? ACTIVE_RUN_POLL_MS : 0),
  })
}

export function useAnswers(identifier: string, unit: string | null, enabled: boolean) {
  return useSWR(
    enabled ? (['answers', identifier, unit] as const) : null,
    () => fetchAnswers(identifier, unit),
    { ...STABLE, keepPreviousData: true },
  )
}

export function useTable(identifier: string, name: string) {
  return useSWR(['table', identifier, name] as const, () => fetchTable(identifier, name), STABLE)
}

export function useComparison(base: string, other: string) {
  return useSWR(['comparison', base, other] as const, () => fetchComparison(base, other), STABLE)
}
