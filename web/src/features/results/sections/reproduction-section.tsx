import { Download } from 'lucide-react'

import { CompareSelector } from '@/features/results/compare-selector'
import { packageUrl } from '@/shared/api/client'
import type { RunRecord } from '@/shared/api/schemas/records'
import { isActive, type RunDetails } from '@/shared/api/schemas/run'
import { primaryButton, secondaryButton } from '@/shared/components/button-styles'
import { type DefinitionRow, DefinitionRows } from '@/shared/components/definition-rows'
import { SectionBlock } from '@/shared/components/section-block'
import { SimpleTable } from '@/shared/components/simple-table'
import { withUnit } from '@/shared/format/labels'
import { RouteLink } from '@/shared/routing/route-link'

type Props = {
  details: RunDetails
  record: RunRecord | null
}

const EXACTNESS = new Map([
  ['exact', 'definição exata do SI'],
  ['measured', 'valor medido'],
])

function versionRows(details: RunDetails, record: RunRecord | null): DefinitionRow[] {
  const { run } = details
  const rows: DefinitionRow[] = [
    { term: 'Identificador', description: <code className="font-mono">{run.identifier}</code> },
    {
      term: 'SHA-256 da entrada',
      description: <code className="font-mono break-all">{run.input_sha256}</code>,
    },
    {
      term: 'SHA-256 do problema canônico',
      description: <code className="font-mono break-all">{run.canonical_problem_sha256}</code>,
    },
    { term: 'Versão da calculadora', description: run.package_version },
  ]
  if (record === null) return rows
  rows.push({ term: 'Esquema do registro', description: record.schema_version })
  if (record.catalog !== undefined) {
    rows.push({ term: 'Catálogo', description: record.catalog.version })
  }
  if (record.constants !== undefined) {
    rows.push({ term: 'Constantes', description: record.constants.edition })
  }
  if (record.units !== undefined) {
    rows.push({ term: 'Registro de unidades', description: record.units.registry_version })
  }
  return rows
}

export function ReproductionSection({ details, record }: Props) {
  const { run } = details
  const constants = record?.constants?.used ?? []
  const environment = record?.environment

  return (
    <SectionBlock title="Reprodução e comparação">
      <div className="flex flex-wrap gap-3">
        {isActive(run) ? null : (
          <a href={packageUrl(run.identifier)} download className={primaryButton}>
            <Download className="size-4" aria-hidden="true" />
            Exportar pacote
          </a>
        )}
        <RouteLink
          to={{ name: 'editor', card: run.card.identifier, from: run.identifier }}
          className={secondaryButton}
        >
          Alterar e recalcular
        </RouteLink>
      </div>
      <CompareSelector run={run} />
      <DefinitionRows rows={versionRows(details, record)} />
      <details>
        <summary className="cursor-pointer text-sm font-medium">Entrada original</summary>
        <pre className="mt-3 max-h-96 overflow-auto border border-rule bg-surface p-3 font-mono text-sm">
          {details.input.text}
        </pre>
      </details>
      {constants.length === 0 ? null : (
        <details>
          <summary className="cursor-pointer text-sm font-medium">Constantes usadas</summary>
          <div className="pt-3">
            <SimpleTable
              caption="Constantes usadas"
              headers={['Símbolo', 'Constante', 'Valor', 'Natureza', 'Fonte']}
              rows={constants.map((constant) => ({
                key: constant.identifier,
                cells: [
                  <span key="symbol" className="font-mono">
                    {constant.symbol}
                  </span>,
                  constant.name,
                  <span key="value" className="font-mono whitespace-nowrap">
                    {withUnit(constant.value.decimal, constant.value.unit)}
                  </span>,
                  EXACTNESS.get(constant.exactness) ?? constant.exactness,
                  <span key="source" className="break-all">
                    {constant.source ?? ''}
                  </span>,
                ],
              }))}
            />
          </div>
        </details>
      )}
      {environment === undefined ? null : (
        <details>
          <summary className="cursor-pointer text-sm font-medium">Ambiente do cálculo</summary>
          <div className="flex flex-col gap-3 pt-3">
            <p className="text-sm">
              {`${environment.python.implementation} ${environment.python.version} em ${environment.platform}.`}
            </p>
            <SimpleTable
              caption="Bibliotecas do ambiente"
              headers={['Biblioteca', 'Versão']}
              rows={[
                ...environment.dependencies.map((dependency) => ({
                  key: dependency.name,
                  cells: [dependency.name, dependency.version],
                })),
                ...environment.linear_algebra.map((library) => ({
                  key: `${library.consumer}:${library.interface}`,
                  cells: [
                    `${library.interface} usado por ${library.consumer}`,
                    `${library.name} ${library.version}`,
                  ],
                })),
              ]}
            />
          </div>
        </details>
      )}
    </SectionBlock>
  )
}
