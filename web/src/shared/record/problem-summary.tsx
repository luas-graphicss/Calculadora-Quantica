import type { ReactNode } from 'react'

import type { ProblemSection } from '@/shared/api/schemas/records'
import { NotatedExpression } from '@/shared/components/notated-expression'
import { SimpleTable } from '@/shared/components/simple-table'
import { describeTerm, unitLabel, withUnit } from '@/shared/format/labels'
import { formatMemory } from '@/shared/format/values'

type Props = {
  problem: ProblemSection
}

type PartProps = {
  title: string
  children: ReactNode
}

const ABSENT = '—'

function Part({ title, children }: PartProps) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold">{title}</h3>
      {children}
    </div>
  )
}

function informed(parameter: ProblemSection['parameters'][number]): string {
  if (parameter.given !== undefined) return withUnit(parameter.given.value, parameter.given.unit)
  if (parameter.constant !== undefined) return `constante ${parameter.constant} do catálogo`
  return parameter.count ?? ABSENT
}

export function ProblemSummary({ problem }: Props) {
  const { requested, uncertainty, estimate } = problem
  const boundaries = [...problem.scope, ...problem.domain]

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-muted">
        {'Ficha '}
        <code className="font-mono text-ink">{problem.card.identifier}</code>
        {`, versão ${problem.card.version}.`}
      </p>
      {problem.statement === null ? null : (
        <Part title="Enunciado lido">
          <NotatedExpression latex={problem.statement.latex} text={problem.statement.text} />
        </Part>
      )}
      {problem.conditions.length === 0 ? null : (
        <Part title="Condições lidas">
          <ul className="flex flex-col gap-3">
            {problem.conditions.map((condition) => (
              <li key={condition.text}>
                <NotatedExpression latex={condition.latex} text={condition.text} />
              </li>
            ))}
          </ul>
        </Part>
      )}
      {problem.candidate === null ? null : (
        <Part title="Candidata lida">
          <NotatedExpression latex={problem.candidate.latex} text={problem.candidate.text} />
        </Part>
      )}
      {problem.symbols.length === 0 ? null : (
        <Part title="Símbolos declarados">
          <SimpleTable
            caption="Símbolos declarados"
            headers={['Símbolo', 'Papel', 'Domínio', 'Unidade', 'Argumento']}
            rows={problem.symbols.map((symbol) => ({
              key: symbol.name,
              cells: [
                <code key="name" className="font-mono">
                  {symbol.name}
                </code>,
                describeTerm(symbol.role),
                describeTerm(symbol.domain),
                unitLabel(symbol.unit),
                symbol.argument ?? ABSENT,
              ],
            }))}
          />
        </Part>
      )}
      {problem.hypotheses.length === 0 ? null : (
        <Part title="Hipóteses confirmadas">
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
            {problem.hypotheses.map((hypothesis) => (
              <li key={hypothesis.key}>{hypothesis.statement}</li>
            ))}
          </ul>
        </Part>
      )}
      {problem.parameters.length === 0 ? null : (
        <Part title="Grandezas">
          <SimpleTable
            caption="Grandezas do problema"
            headers={['Grandeza', 'Informado', 'Em unidades do SI']}
            rows={problem.parameters.map((parameter) => ({
              key: parameter.name,
              cells: [
                <code key="symbol" className="font-mono">
                  {parameter.symbol}
                </code>,
                <span key="given" className="font-mono">
                  {informed(parameter)}
                </span>,
                <span key="si" className="font-mono">
                  {parameter.si === undefined
                    ? ABSENT
                    : withUnit(parameter.si.decimal, parameter.si.unit)}
                </span>,
              ],
            }))}
          />
        </Part>
      )}
      {problem.inputs.length === 0 ? null : (
        <Part title="Dados lidos">
          <SimpleTable
            caption="Dados lidos da entrada"
            headers={['Dado', 'Valor', 'Origem']}
            rows={problem.inputs.map((input) => ({
              key: input.name,
              cells: [
                input.label,
                <span key="value" className="font-mono">
                  {input.value}
                </span>,
                input.origin ?? ABSENT,
              ],
            }))}
          />
        </Part>
      )}
      {problem.resolution.length === 0 ? null : (
        <Part title="Resolução numérica">
          <SimpleTable
            caption="Resolução numérica pedida"
            headers={['Ajuste', 'Valor']}
            rows={problem.resolution.map((setting) => ({
              key: setting.name,
              cells: [
                setting.label,
                <span key="value" className="font-mono">
                  {setting.value}
                </span>,
              ],
            }))}
          />
        </Part>
      )}
      {requested === undefined ? null : (
        <Part title="Grandeza pedida">
          <p className="text-sm">
            {`${requested.label} (${requested.symbol}), em ${unitLabel(requested.unit)}, com ` +
              `${requested.significant_digits} algarismos significativos.`}
          </p>
        </Part>
      )}
      {uncertainty === null ? null : (
        <Part title="Incertezas declaradas">
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
            <li>{`Covariância: ${describeTerm(uncertainty.covariance)}.`}</li>
            {uncertainty.standard_uncertainties.map((item) => (
              <li key={item.parameter}>
                {`Incerteza padrão de ${item.parameter}: `}
                <span className="font-mono">{withUnit(item.given.value, item.given.unit)}</span>
              </li>
            ))}
          </ul>
        </Part>
      )}
      {estimate === undefined ? null : (
        <Part title="Custo estimado antes de calcular">
          <p className="text-sm">
            {`Memória: ${formatMemory(estimate.memory_bytes)}. Operações: ` +
              `${estimate.operations.toLocaleString('pt-BR')}.`}
          </p>
        </Part>
      )}
      {boundaries.length === 0 ? null : (
        <Part title="Alcance da ficha">
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
            {boundaries.map((boundary) => (
              <li key={boundary}>{boundary}</li>
            ))}
          </ul>
        </Part>
      )}
    </div>
  )
}
