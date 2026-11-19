import { isStrictlyIncreasing } from '@/shared/charts/chart-scale'

export type Column = {
  name: string
  symbol: string
  unit: string
  values: readonly number[]
}

export type SeriesGroup = {
  unit: string
  abscissa: Column
  series: Column[]
}

const SMALLEST_SERIES = 3

export function seriesGroups(columns: readonly Column[]): SeriesGroup[] {
  const [abscissa, ...ordinates] = columns
  if (abscissa === undefined || ordinates.length === 0) return []
  if (abscissa.values.length < SMALLEST_SERIES || !isStrictlyIncreasing(abscissa.values)) return []
  const byUnit = new Map<string, Column[]>()
  for (const column of ordinates) {
    const group = byUnit.get(column.unit)
    if (group === undefined) byUnit.set(column.unit, [column])
    else group.push(column)
  }
  return [...byUnit].map(([unit, series]) => ({ unit, abscissa, series }))
}
