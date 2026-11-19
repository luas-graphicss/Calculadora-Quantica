import { ComparedRun } from '@/features/history/compared-run'
import { useCatalog, useComparison } from '@/shared/api/queries'
import { findChoice } from '@/shared/api/schemas/catalog'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { Notice } from '@/shared/components/notice'
import { PageHeading } from '@/shared/components/page-heading'
import { SectionBlock } from '@/shared/components/section-block'
import { SimpleTable } from '@/shared/components/simple-table'
import { withUnit } from '@/shared/format/labels'
import { describePointer } from '@/shared/format/pointers'
import { usePageTitle } from '@/shared/hooks/use-page-title'

type Props = {
  base: string
  other: string
}

const ABSENT = 'ausente'
const SIDES = ['Base', 'Comparada'] as const

function shown(value: string | null): string {
  return value ?? ABSENT
}

export function ComparisonPage({ base, other }: Props) {
  usePageTitle('Comparação')
  const comparison = useComparison(base, other)
  const catalog = useCatalog()

  if (comparison.data === undefined) {
    return comparison.error === undefined ? (
      <LoadingLine label="Carregando a comparação" />
    ) : (
      <ErrorNotice error={comparison.error} />
    )
  }
  const compared = comparison.data
  const form =
    catalog.data === undefined
      ? undefined
      : findChoice(catalog.data, compared.base.card.identifier)?.choice.form
  const { method } = compared

  return (
    <div className="flex flex-col gap-8">
      <PageHeading title="Comparação de execuções" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <ComparedRun side="Base" run={compared.base} />
        <ComparedRun side="Comparada" run={compared.other} />
      </div>
      <SectionBlock title="Versões">
        {compared.version_divergences.length === 0 ? (
          <p className="text-sm">
            As duas execuções registram as mesmas versões de calculadora, ficha, catálogo,
            constantes e bibliotecas.
          </p>
        ) : (
          <>
            <Notice tone="problem" title="As execuções usaram versões diferentes">
              Uma diferença de versão pode explicar uma diferença de resultado. Leve isto em conta
              antes de comparar os números.
            </Notice>
            <SimpleTable
              caption="Divergências de versão"
              headers={['O que mudou', ...SIDES]}
              rows={compared.version_divergences.map((divergence) => ({
                key: divergence.subject,
                cells: [
                  divergence.subject,
                  <span key="base" className="font-mono">
                    {shown(divergence.base)}
                  </span>,
                  <span key="other" className="font-mono">
                    {shown(divergence.other)}
                  </span>,
                ],
              }))}
            />
          </>
        )}
      </SectionBlock>
      <SectionBlock title="Diferenças na entrada">
        {compared.input_differences.length === 0 ? (
          <p className="text-sm">As duas entradas são iguais.</p>
        ) : (
          <SimpleTable
            caption="Diferenças na entrada"
            headers={['Campo', ...SIDES]}
            rows={compared.input_differences.map((difference) => ({
              key: difference.pointer,
              cells: [
                describePointer(difference.pointer, form),
                <span key="base" className="font-mono">
                  {shown(difference.base)}
                </span>,
                <span key="other" className="font-mono">
                  {shown(difference.other)}
                </span>,
              ],
            }))}
          />
        )}
      </SectionBlock>
      <SectionBlock title="Método">
        {method.base === method.other ? (
          <p className="text-sm">
            {'As duas execuções usaram o método '}
            <code className="font-mono">{shown(method.base)}</code>.
          </p>
        ) : (
          <SimpleTable
            caption="Método de cada execução"
            headers={SIDES}
            rows={[
              {
                key: 'method',
                cells: [
                  <code key="base" className="font-mono">
                    {shown(method.base)}
                  </code>,
                  <code key="other" className="font-mono">
                    {shown(method.other)}
                  </code>,
                ],
              },
            ]}
          />
        )}
      </SectionBlock>
      <SectionBlock title="Respostas">
        {compared.answers.length === 0 ? (
          <p className="text-sm">Nenhuma das execuções tem resposta numérica para comparar.</p>
        ) : (
          <SimpleTable
            caption="Respostas das duas execuções"
            headers={['Grandeza', ...SIDES, 'Razão comparada / base']}
            rows={compared.answers.map((answer) => ({
              key: answer.name,
              cells: [
                <span key="label">
                  {answer.label}{' '}
                  <span className="font-mono text-muted">{`(${answer.symbol})`}</span>
                </span>,
                <span key="base" className="font-mono whitespace-nowrap tabular-nums">
                  {answer.base === null ? ABSENT : withUnit(answer.base.value, answer.base.unit)}
                </span>,
                <span key="other" className="font-mono whitespace-nowrap tabular-nums">
                  {answer.other === null ? ABSENT : withUnit(answer.other.value, answer.other.unit)}
                </span>,
                <span key="ratio" className="font-mono font-medium tabular-nums">
                  {answer.ratio ?? 'não calculada'}
                </span>,
              ],
            }))}
          />
        )}
      </SectionBlock>
    </div>
  )
}
