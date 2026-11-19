export type Extent = {
  min: number
  max: number
}

const FLAT_PADDING_RATIO = 0.1
const TICK_TOLERANCE = 1e-9
const PLAIN_FROM = 1e-3
const PLAIN_BELOW = 1e5
const TICK_DIGITS = 4

export function extentOf(values: readonly number[]): Extent | null {
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY
  for (const value of values) {
    if (!Number.isFinite(value)) continue
    if (value < min) min = value
    if (value > max) max = value
  }
  return min <= max ? { min, max } : null
}

export function mergeExtents(extents: readonly (Extent | null)[]): Extent | null {
  const known = extents.filter((extent): extent is Extent => extent !== null)
  if (known.length === 0) return null
  return {
    min: Math.min(...known.map((extent) => extent.min)),
    max: Math.max(...known.map((extent) => extent.max)),
  }
}

export function widenFlatExtent(extent: Extent): Extent {
  if (extent.min !== extent.max) return extent
  const padding = extent.min === 0 ? 1 : Math.abs(extent.min) * FLAT_PADDING_RATIO
  return { min: extent.min - padding, max: extent.max + padding }
}

export function niceTicks(extent: Extent, target: number): number[] {
  const span = extent.max - extent.min
  if (!(span > 0)) return [extent.min]
  const rough = span / Math.max(1, target)
  const power = 10 ** Math.floor(Math.log10(rough))
  const fraction = rough / power
  const multiple = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10
  const step = multiple * power
  const first = Math.ceil(extent.min / step - TICK_TOLERANCE)
  const last = Math.floor(extent.max / step + TICK_TOLERANCE)
  const ticks: number[] = []
  for (let index = first; index <= last; index += 1) {
    ticks.push(index === 0 ? 0 : index * step)
  }
  return ticks
}

export function linearScale(domain: Extent, range: Extent): (value: number) => number {
  const span = domain.max - domain.min
  return (value) => range.min + ((value - domain.min) / span) * (range.max - range.min)
}

export function formatTick(value: number): string {
  if (value === 0) return '0'
  const magnitude = Math.abs(value)
  if (magnitude >= PLAIN_FROM && magnitude < PLAIN_BELOW) {
    return String(Number(value.toPrecision(TICK_DIGITS)))
  }
  return value.toExponential(1).replace('e+', 'e')
}

export function isStrictlyIncreasing(values: readonly number[]): boolean {
  let previous = Number.NEGATIVE_INFINITY
  for (const value of values) {
    if (!(value > previous)) return false
    previous = value
  }
  return values.length > 0
}
