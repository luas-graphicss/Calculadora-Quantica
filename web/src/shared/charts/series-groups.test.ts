import { describe, expect, it } from 'vitest'

import { type Column, seriesGroups } from '@/shared/charts/series-groups'

function column(name: string, unit: string, values: number[]): Column {
  return { name, symbol: name, unit, values }
}

const POSITION = column('x', 'm', [0, 1, 2])

describe('seriesGroups', () => {
  it('draws the amplitude and the density on separate axes, one per unit', () => {
    const groups = seriesGroups([
      POSITION,
      column('re_psi', 'm^(-1/2)', [0, 1, 0]),
      column('im_psi', 'm^(-1/2)', [0, 0, 0]),
      column('density', '1/m', [0, 1, 0]),
    ])

    expect(groups.map((group) => [group.unit, group.series.map((series) => series.name)])).toEqual([
      ['m^(-1/2)', ['re_psi', 'im_psi']],
      ['1/m', ['density']],
    ])
    expect(groups.every((group) => group.abscissa === POSITION)).toBe(true)
  })

  it('leaves a table without a growing abscissa as a table', () => {
    const levels = column('level', '1', [1, 1, 2])
    expect(seriesGroups([levels, column('E', 'eV', [1, 2, 3])])).toEqual([])
  })

  it('does not draw fewer than three points', () => {
    expect(seriesGroups([column('x', 'm', [0, 1]), column('y', 'm', [0, 1])])).toEqual([])
  })

  it('has nothing to draw with a single column', () => {
    expect(seriesGroups([POSITION])).toEqual([])
    expect(seriesGroups([])).toEqual([])
  })
})
