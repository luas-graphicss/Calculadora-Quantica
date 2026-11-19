import { MathExpression } from '@/shared/components/math-expression'

type Props = {
  latex: string
  text: string
}

export function NotatedExpression({ latex, text }: Props) {
  return (
    <div className="flex flex-col gap-1">
      <MathExpression latex={latex} block />
      <p className="text-sm text-muted">
        {'Em texto: '}
        <code className="font-mono text-ink">{text}</code>
      </p>
    </div>
  )
}
