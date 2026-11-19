import type { CalculationStep, RunRecord } from '@/shared/api/schemas/records'
import { MathExpression } from '@/shared/components/math-expression'
import { NotatedExpression } from '@/shared/components/notated-expression'
import { SectionBlock } from '@/shared/components/section-block'
import { SimpleTable } from '@/shared/components/simple-table'
import { withUnit } from '@/shared/format/labels'
import { PlanSummary } from '@/shared/record/plan-summary'

type Props = {
  record: RunRecord
}

type StepProps = {
  step: CalculationStep
}

function Step({ step }: StepProps) {
  const { expression, value } = step
  return (
    <li className="flex flex-col gap-1">
      <p className="text-sm">{step.description}</p>
      {typeof expression === 'string' ? (
        <code className="font-mono text-sm break-words">{expression}</code>
      ) : (
        <div className="flex flex-col gap-1">
          <MathExpression latex={expression.latex} block />
          <code className="font-mono text-sm break-words text-muted">{expression.text}</code>
        </div>
      )}
      {value === null ? null : (
        <p className="font-mono text-sm break-words">{`= ${withUnit(value.decimal, value.unit)}`}</p>
      )}
    </li>
  )
}

export function MethodSection({ record }: Props) {
  const { result } = record
  return (
    <SectionBlock title="Método">
      <PlanSummary plan={record.plan} />
      {result.steps.length === 0 ? null : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Memória de cálculo</h3>
          <ol className="flex list-decimal flex-col gap-4 pl-5">
            {result.steps.map((step) => (
              <Step key={step.description} step={step} />
            ))}
          </ol>
        </div>
      )}
      {result.certificate === null ? null : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Primitiva usada</h3>
          <NotatedExpression latex={result.certificate.latex} text={result.certificate.text} />
        </div>
      )}
      {result.si_value === undefined ? null : (
        <p className="text-sm">
          {'Valor em unidades do SI: '}
          <span className="font-mono">
            {withUnit(result.si_value.decimal, result.si_value.unit)}
          </span>
        </p>
      )}
      {result.effective.length === 0 ? null : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Parâmetros efetivos do cálculo</h3>
          <SimpleTable
            caption="Parâmetros efetivos do cálculo"
            headers={['Parâmetro', 'Valor']}
            rows={result.effective.map((item) => ({
              key: item.name,
              cells: [
                item.label,
                <span key="value" className="font-mono">
                  {item.value}
                </span>,
              ],
            }))}
          />
        </div>
      )}
    </SectionBlock>
  )
}
