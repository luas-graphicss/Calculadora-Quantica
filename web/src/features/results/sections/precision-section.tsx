import type { DisplayedAnswer } from '@/shared/api/schemas/answers'
import type { RunRecord } from '@/shared/api/schemas/records'
import { type DefinitionRow, DefinitionRows } from '@/shared/components/definition-rows'
import { SectionBlock } from '@/shared/components/section-block'
import { SimpleTable } from '@/shared/components/simple-table'
import { describeNature, describeTerm, unitLabel, withUnit } from '@/shared/format/labels'
import { describeRounding } from '@/shared/record/plan-summary'

type Props = {
  record: RunRecord
  answers: readonly DisplayedAnswer[]
}

const NOT_EVALUATED = 'not_evaluated'

function uncertaintyRows(uncertainty: NonNullable<RunRecord['result']['uncertainty']>) {
  const rows: DefinitionRow[] = []
  if (uncertainty.status === NOT_EVALUATED) {
    rows.push({
      term: 'Incerteza dos dados',
      description: `Incerteza não avaliada. ${uncertainty.reason ?? ''}`.trim(),
    })
    return rows
  }
  if (uncertainty.standard_uncertainty !== undefined) {
    rows.push({
      term: 'Incerteza padrão propagada',
      description: (
        <span className="font-mono">
          {withUnit(
            uncertainty.standard_uncertainty.decimal,
            uncertainty.standard_uncertainty.unit,
          )}
        </span>
      ),
    })
  }
  if (uncertainty.relative_standard_uncertainty !== undefined) {
    rows.push({
      term: 'Incerteza padrão relativa',
      description: <span className="font-mono">{uncertainty.relative_standard_uncertainty}</span>,
    })
  }
  if (uncertainty.covariance !== undefined) {
    rows.push({ term: 'Covariância declarada', description: describeTerm(uncertainty.covariance) })
  }
  return rows
}

export function PrecisionSection({ record, answers }: Props) {
  const { result, plan, problem } = record
  const rounding = plan.rounding ?? problem.rounding
  const estimated = answers.filter((answer) => answer.error !== null)
  const rows: DefinitionRow[] = [
    { term: 'Natureza da resposta', description: describeNature(result.nature) },
  ]
  if (rounding !== undefined) {
    rows.push({ term: 'Arredondamento exibido', description: describeRounding(rounding) })
  }
  if (result.uncertainty !== undefined) rows.push(...uncertaintyRows(result.uncertainty))
  const contributions = result.uncertainty?.contributions ?? []

  return (
    <SectionBlock title="Precisão">
      <DefinitionRows rows={rows} />
      {estimated.length === 0 ? null : (
        <SimpleTable
          caption="Erro estimado de cada resposta"
          headers={['Resposta', 'Erro estimado', 'Como foi estimado']}
          rows={estimated.map((answer) => ({
            key: answer.name,
            cells: [
              <span key="symbol" className="font-mono whitespace-nowrap">
                {answer.symbol}
              </span>,
              <span key="error" className="font-mono whitespace-nowrap">
                {`${answer.error ?? ''} ${unitLabel(answer.unit)}`}
              </span>,
              answer.error_origin ?? '',
            ],
          }))}
        />
      )}
      {contributions.length === 0 ? null : (
        <SimpleTable
          caption="Contribuição de cada dado para a incerteza"
          headers={['Dado', 'Incerteza padrão', 'Sensibilidade']}
          rows={contributions.map((contribution) => ({
            key: contribution.parameter,
            cells: [
              <span key="symbol" className="font-mono">
                {contribution.symbol}
              </span>,
              <span key="uncertainty" className="font-mono">
                {withUnit(
                  contribution.standard_uncertainty.decimal,
                  contribution.standard_uncertainty.unit,
                )}
              </span>,
              <span key="sensitivity" className="font-mono break-all">
                {withUnit(contribution.sensitivity.decimal, contribution.sensitivity.unit)}
              </span>,
            ],
          }))}
        />
      )}
      {result.warnings.length === 0 ? null : (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Avisos do método</h3>
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </SectionBlock>
  )
}
