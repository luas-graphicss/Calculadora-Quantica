import { describe, expect, it } from 'vitest'

import { formatRoute, parseRoute, type Route } from '@/shared/routing/routes'

const RUN = '0123456789abcdef0123456789abcdef'
const OTHER = 'fedcba9876543210fedcba9876543210'
const CARD = 'quantum.infinite_square_well.energy_level'

describe('parseRoute', () => {
  it('opens the catalog for an empty location', () => {
    expect(parseRoute('')).toEqual({ name: 'catalog' })
    expect(parseRoute('#/')).toEqual({ name: 'catalog' })
  })

  it.each<[string, Route]>([
    ['#/historico', { name: 'history' }],
    [`#/formular/${CARD}`, { name: 'editor', card: CARD, from: null }],
    [`#/formular/${CARD}?de=${RUN}`, { name: 'editor', card: CARD, from: RUN }],
    [`#/execucoes/${RUN}`, { name: 'run', identifier: RUN }],
    [`#/comparar/${RUN}/${OTHER}`, { name: 'comparison', base: RUN, other: OTHER }],
  ])('reads %s', (hash, route) => {
    expect(parseRoute(hash)).toEqual(route)
  })

  it.each([
    '#/execucoes/not-a-run',
    `#/execucoes/${RUN.toUpperCase()}`,
    '#/formular/Bad Card',
    `#/formular/${CARD}?de=..%2F..%2Fsecret`,
    '#/historico/extra',
    `#/comparar/${RUN}`,
    `#/comparar/${RUN}/${OTHER}/extra`,
    '#/desconhecida',
  ])('refuses %s', (hash) => {
    expect(parseRoute(hash)).toEqual({ name: 'unknown' })
  })
})

describe('formatRoute', () => {
  it('writes a location that parses back to the same route', () => {
    const routes: Route[] = [
      { name: 'catalog' },
      { name: 'history' },
      { name: 'editor', card: CARD, from: null },
      { name: 'editor', card: CARD, from: RUN },
      { name: 'run', identifier: RUN },
      { name: 'comparison', base: RUN, other: OTHER },
    ]

    for (const route of routes) {
      expect(parseRoute(formatRoute(route))).toEqual(route)
    }
  })
})
