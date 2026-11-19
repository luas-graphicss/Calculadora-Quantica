export type Route =
  | { name: 'catalog' }
  | { name: 'editor'; card: string; from: string | null }
  | { name: 'run'; identifier: string }
  | { name: 'history' }
  | { name: 'comparison'; base: string; other: string }
  | { name: 'unknown' }

const RUN_IDENTIFIER = /^[0-9a-f]{32}$/
const CARD_IDENTIFIER = /^[a-z0-9_.]{1,128}$/
const UNKNOWN: Route = { name: 'unknown' }

export function parseRoute(hash: string): Route {
  const [path = '', query = ''] = hash.replace(/^#/, '').split('?')
  const segments = path.split('/').filter((segment) => segment !== '')
  const [section, first, second, ...rest] = segments
  if (section === undefined) return { name: 'catalog' }
  if (rest.length > 0) return UNKNOWN
  if (section === 'historico' && first === undefined) return { name: 'history' }
  if (section === 'formular' && first !== undefined && second === undefined) {
    const from = new URLSearchParams(query).get('de')
    if (!CARD_IDENTIFIER.test(first)) return UNKNOWN
    if (from !== null && !RUN_IDENTIFIER.test(from)) return UNKNOWN
    return { name: 'editor', card: first, from }
  }
  if (section === 'execucoes' && first !== undefined && second === undefined) {
    return RUN_IDENTIFIER.test(first) ? { name: 'run', identifier: first } : UNKNOWN
  }
  if (section === 'comparar' && first !== undefined && second !== undefined) {
    const areRuns = RUN_IDENTIFIER.test(first) && RUN_IDENTIFIER.test(second)
    return areRuns ? { name: 'comparison', base: first, other: second } : UNKNOWN
  }
  return UNKNOWN
}

export function formatRoute(route: Route): string {
  switch (route.name) {
    case 'catalog':
    case 'unknown':
      return '#/'
    case 'history':
      return '#/historico'
    case 'editor':
      return route.from === null
        ? `#/formular/${route.card}`
        : `#/formular/${route.card}?${new URLSearchParams({ de: route.from }).toString()}`
    case 'run':
      return `#/execucoes/${route.identifier}`
    case 'comparison':
      return `#/comparar/${route.base}/${route.other}`
  }
}
