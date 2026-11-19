import {
  extentOf,
  formatTick,
  linearScale,
  mergeExtents,
  niceTicks,
  widenFlatExtent,
} from '@/shared/charts/chart-scale'
import type { SeriesGroup } from '@/shared/charts/series-groups'
import { unitLabel } from '@/shared/format/labels'

type Props = {
  group: SeriesGroup
}

const WIDTH = 640
const HEIGHT = 320
const MARGIN = { top: 12, right: 16, bottom: 46, left: 76 }
const PLOT = {
  left: MARGIN.left,
  right: WIDTH - MARGIN.right,
  top: MARGIN.top,
  bottom: HEIGHT - MARGIN.bottom,
}
const TICK_LENGTH = 5
const X_TICKS = 6
const Y_TICKS = 5
const STROKES = [
  { dash: undefined, tone: 'stroke-primary' },
  { dash: '7 4', tone: 'stroke-ink' },
  { dash: '2 3', tone: 'stroke-primary' },
  { dash: '11 3 2 3', tone: 'stroke-ink' },
] as const

function strokeFor(index: number) {
  return STROKES[index % STROKES.length] ?? STROKES[0]
}

function polylinePoints(
  xs: readonly number[],
  ys: readonly number[],
  toX: (value: number) => number,
  toY: (value: number) => number,
): string {
  const points: string[] = []
  xs.forEach((x, index) => {
    const y = ys[index]
    if (y === undefined || !Number.isFinite(x) || !Number.isFinite(y)) return
    points.push(`${toX(x).toFixed(2)},${toY(y).toFixed(2)}`)
  })
  return points.join(' ')
}

export function LineChart({ group }: Props) {
  const { abscissa, series, unit } = group
  const xExtent = extentOf(abscissa.values)
  const yExtent = mergeExtents(series.map((column) => extentOf(column.values)))
  if (xExtent === null || yExtent === null) return null

  const xDomain = widenFlatExtent(xExtent)
  const yDomain = widenFlatExtent(yExtent)
  const toX = linearScale(xDomain, { min: PLOT.left, max: PLOT.right })
  const toY = linearScale(yDomain, { min: PLOT.bottom, max: PLOT.top })
  const symbols = series.map((column) => column.symbol).join(', ')
  const summary =
    `Gráfico de ${symbols}, em ${unitLabel(unit)}, em função de ${abscissa.symbol}, ` +
    `em ${unitLabel(abscissa.unit)}. Os mesmos dados estão na tabela desta seção.`

  return (
    <figure className="flex flex-col gap-2">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={summary}
        className="h-auto w-full border border-rule bg-surface"
      >
        {niceTicks(yDomain, Y_TICKS).map((tick) => (
          <g key={`y${tick}`}>
            <line
              x1={PLOT.left}
              x2={PLOT.right}
              y1={toY(tick)}
              y2={toY(tick)}
              className="stroke-rule"
              strokeWidth={1}
            />
            <text
              x={PLOT.left - TICK_LENGTH - 3}
              y={toY(tick)}
              textAnchor="end"
              dominantBaseline="middle"
              className="fill-muted font-mono text-[11px]"
            >
              {formatTick(tick)}
            </text>
          </g>
        ))}
        {niceTicks(xDomain, X_TICKS).map((tick) => (
          <g key={`x${tick}`}>
            <line
              x1={toX(tick)}
              x2={toX(tick)}
              y1={PLOT.bottom}
              y2={PLOT.bottom + TICK_LENGTH}
              className="stroke-rule-strong"
              strokeWidth={1}
            />
            <text
              x={toX(tick)}
              y={PLOT.bottom + TICK_LENGTH + 12}
              textAnchor="middle"
              className="fill-muted font-mono text-[11px]"
            >
              {formatTick(tick)}
            </text>
          </g>
        ))}
        <line
          x1={PLOT.left}
          x2={PLOT.right}
          y1={PLOT.bottom}
          y2={PLOT.bottom}
          className="stroke-rule-strong"
          strokeWidth={1}
        />
        <line
          x1={PLOT.left}
          x2={PLOT.left}
          y1={PLOT.top}
          y2={PLOT.bottom}
          className="stroke-rule-strong"
          strokeWidth={1}
        />
        {series.map((column, index) => (
          <polyline
            key={column.name}
            points={polylinePoints(abscissa.values, column.values, toX, toY)}
            fill="none"
            strokeWidth={1.75}
            strokeDasharray={strokeFor(index).dash}
            strokeLinejoin="round"
            className={strokeFor(index).tone}
          />
        ))}
        <text
          x={(PLOT.left + PLOT.right) / 2}
          y={HEIGHT - 8}
          textAnchor="middle"
          className="fill-ink text-[12px]"
        >
          {`${abscissa.symbol} (${unitLabel(abscissa.unit)})`}
        </text>
        <text
          x={14}
          y={(PLOT.top + PLOT.bottom) / 2}
          textAnchor="middle"
          transform={`rotate(-90 14 ${(PLOT.top + PLOT.bottom) / 2})`}
          className="fill-ink text-[12px]"
        >
          {unitLabel(unit)}
        </text>
      </svg>
      <figcaption>
        <ul className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          {series.map((column, index) => (
            <li key={column.name} className="flex items-center gap-2">
              <svg viewBox="0 0 36 8" className="h-2 w-9" aria-hidden="true">
                <line
                  x1={0}
                  x2={36}
                  y1={4}
                  y2={4}
                  strokeWidth={2}
                  strokeDasharray={strokeFor(index).dash}
                  className={strokeFor(index).tone}
                />
              </svg>
              <span className="font-mono">{column.symbol}</span>
            </li>
          ))}
        </ul>
      </figcaption>
    </figure>
  )
}
