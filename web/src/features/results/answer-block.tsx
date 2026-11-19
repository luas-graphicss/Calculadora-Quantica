import { useId } from 'react'

import { VerdictNotice } from '@/features/results/verdict-notice'
import type { Answers, DisplayedAnswer } from '@/shared/api/schemas/answers'
import type { RunRecord } from '@/shared/api/schemas/records'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { MathExpression } from '@/shared/components/math-expression'
import { NotatedExpression } from '@/shared/components/notated-expression'
import { SelectField } from '@/shared/components/select-field'
import { SimpleTable } from '@/shared/components/simple-table'
import { unitLabel } from '@/shared/format/labels'

type Props = {
  record: RunRecord
  answers: Answers | undefined
  answersError: unknown
  displayUnits: readonly string[]
  unit: string | null
  onUnitChange: (unit: string | null) => void
}

type SingleProps = {
  answer: DisplayedAnswer
}

const AS_RECORDED = ''

function SingleAnswer({ answer }: SingleProps) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm text-muted">{answer.label}</p>
      <p className="font-mono text-2xl leading-tight font-medium break-words tabular-nums md:text-4xl">
        <span className="text-muted">{`${answer.symbol} = `}</span>
        {answer.value}
        <span className="text-xl md:text-2xl">{` ${unitLabel(answer.unit)}`}</span>
      </p>
      {answer.error === null ? null : (
        <p className="text-sm">
          <span className="font-mono">{`± ${answer.error} ${unitLabel(answer.unit)}`}</span>
          {answer.error_origin === null ? null : (
            <span className="text-muted">{` · ${answer.error_origin}`}</span>
          )}
        </p>
      )}
    </div>
  )
}

export function AnswerBlock({
  record,
  answers,
  answersError,
  displayUnits,
  unit,
  onUnitChange,
}: Props) {
  const headingId = useId()
  const { result } = record
  const listed = answers?.answers ?? []
  const [single] = listed

  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-5">
      <h2 id={headingId} className="text-sm font-semibold tracking-wide uppercase">
        Resposta
      </h2>
      <VerdictNotice verification={record.verification} />
      <div className="flex flex-col gap-4 border-y-2 border-ink py-5">
        {answers === undefined && answersError === undefined ? (
          <LoadingLine label="Carregando a resposta" />
        ) : null}
        {answersError === undefined ? null : <ErrorNotice error={answersError} />}
        {listed.length === 1 && single !== undefined ? <SingleAnswer answer={single} /> : null}
        {listed.length > 1 ? (
          <SimpleTable
            caption="Respostas"
            headers={['Grandeza', 'Símbolo', 'Valor', 'Unidade', 'Erro estimado']}
            rows={listed.map((answer) => ({
              key: answer.name,
              cells: [
                answer.label,
                <span key="symbol" className="font-mono whitespace-nowrap">
                  {answer.symbol}
                </span>,
                <span key="value" className="font-mono text-base font-medium tabular-nums">
                  {answer.value}
                </span>,
                unitLabel(answer.unit),
                answer.error === null ? (
                  'não estimado'
                ) : (
                  <span key="error" className="font-mono tabular-nums">{`± ${answer.error}`}</span>
                ),
              ],
            }))}
          />
        ) : null}
        {result.answer === undefined ? null : (
          <div className="flex flex-col gap-2 text-lg">
            <NotatedExpression latex={result.answer.latex} text={result.answer.text} />
            {result.unit === undefined ? null : (
              <p className="text-sm text-muted">{`Unidade do resultado: ${unitLabel(result.unit)}.`}</p>
            )}
          </div>
        )}
        {result.expression === undefined ? null : (
          <p className="text-sm">
            <span className="text-muted">{'Expressão usada: '}</span>
            <MathExpression latex={result.expression.latex} />
            <span className="sr-only">{` (em texto: ${result.expression.plain})`}</span>
          </p>
        )}
      </div>
      {displayUnits.length === 0 ? null : (
        <div className="grid grid-cols-1 md:grid-cols-3">
          <SelectField
            label="Unidade de exibição"
            value={unit ?? AS_RECORDED}
            placeholder="como foi registrada"
            hint="A conversão usa o valor guardado. O cálculo não é refeito."
            options={displayUnits.map((item) => ({ value: item, label: item }))}
            onChange={(chosen) => {
              onUnitChange(chosen === AS_RECORDED ? null : chosen)
            }}
          />
        </div>
      )}
    </section>
  )
}
