import { describe, expect, it } from 'vitest'

import {
  extentOf,
  formatTick,
  isStrictlyIncreasing,
  linearScale,
  mergeExtents,
  niceTicks,
  widenFlatExtent,
} from '@/shared/charts/chart-scale'

describe('extentOf', () => {
  it('ignores values that are not finite', () => {
    expect(extentOf([Number.NaN, 2, Number.POSITIVE_INFINITY, -3])).toEqual({ min: -3, max: 2 })
  })

  it('has no extent without a finite value', () => {
    expect(extentOf([])).toBeNull()
    expect(extentOf([Number.NaN])).toBeNull()
  })
})

describe('mergeExtents', () => {
  it('spans every known extent', () => {
    expect(mergeExtents([{ min: 0, max: 1 }, null, { min: -2, max: 0.5 }])).toEqual({
      min: -2,
      max: 1,
    })
  })

  it('is unknown when no series has an extent', () => {
    expect(mergeExtents([null, null])).toBeNull()
  })
})

describe('widenFlatExtent', () => {
  it('gives a constant series room to be drawn', () => {
    expect(widenFlatExtent({ min: 5, max: 5 })).toEqual({ min: 4.5, max: 5.5 })
    expect(widenFlatExtent({ min: 0, max: 0 })).toEqual({ min: -1, max: 1 })
  })

  it('keeps an extent that already has a span', () => {
    const extent = { min: 1, max: 2 }
    expect(widenFlatExtent(extent)).toBe(extent)
  })
})

describe('niceTicks', () => {
  it('uses steps of 1, 2 or 5 times a power of ten', () => {
    expect(niceTicks({ min: 0, max: 10 }, 5)).toEqual([0, 2, 4, 6, 8, 10])
    expect(niceTicks({ min: -44000, max: 44000 }, 5)).toEqual([-40000, -20000, 0, 20000, 40000])
  })

  it('never writes a negative zero', () => {
    const [, middle] = niceTicks({ min: -1, max: 1 }, 2)
    expect(Object.is(middle, 0)).toBe(true)
  })

  it('has a single tick for an extent without span', () => {
    expect(niceTicks({ min: 3, max: 3 }, 5)).toEqual([3])
  })
})

describe('linearScale', () => {
  it('maps the domain onto the range, inverted ranges included', () => {
    const toPixels = linearScale({ min: 0, max: 10 }, { min: 200, max: 0 })
    expect(toPixels(0)).toBe(200)
    expect(toPixels(10)).toBe(0)
    expect(toPixels(2.5)).toBe(150)
  })
})

describe('formatTick', () => {
  it('writes ordinary magnitudes plainly and the rest with an exponent', () => {
    expect(formatTick(0)).toBe('0')
    expect(formatTick(40000)).toBe('40000')
    expect(formatTick(0.25)).toBe('0.25')
    expect(formatTick(2e-10)).toBe('2.0e-10')
    expect(formatTick(-3.5e7)).toBe('-3.5e7')
  })
})

describe('isStrictlyIncreasing', () => {
  it('accepts only an abscissa that always grows', () => {
    expect(isStrictlyIncreasing([0, 1, 2])).toBe(true)
    expect(isStrictlyIncreasing([0, 1, 1])).toBe(false)
    expect(isStrictlyIncreasing([2, 1])).toBe(false)
    expect(isStrictlyIncreasing([0, Number.NaN])).toBe(false)
    expect(isStrictlyIncreasing([])).toBe(false)
  })
})
