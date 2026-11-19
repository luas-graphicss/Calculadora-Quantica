import { Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'

import type { DraftFieldProps } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import {
  type SymbolRow,
  type SymbolRows,
  symbolRowsFrom,
  symbolsFromRows,
  takesArgument,
  takesValue,
  withBlankRow,
} from '@/features/editor/symbol-rows'
import type { Vocabulary } from '@/shared/api/schemas/catalog'
import { secondaryButton } from '@/shared/components/button-styles'
import { SelectField } from '@/shared/components/select-field'
import { TextField } from '@/shared/components/text-field'
import { describeTerm } from '@/shared/format/labels'

type Props = DraftFieldProps & {
  vocabulary: Vocabulary
  symbolsCarryValues: boolean
}

function termOptions(terms: readonly string[]) {
  return terms.map((term) => ({ value: term, label: describeTerm(term) }))
}

export function SymbolTable({ vocabulary, symbolsCarryValues, draft, onChange }: Props) {
  const [table, setTable] = useState(() => symbolRowsFrom(draft))
  const { rows } = table
  const error = useFieldError('/symbols')

  function commit(updated: SymbolRows) {
    setTable(updated)
    onChange(['symbols'], symbolsFromRows(updated.rows, symbolsCarryValues))
  }

  function change(id: string, fields: Partial<SymbolRow>) {
    commit({ ...table, rows: rows.map((row) => (row.id === id ? { ...row, ...fields } : row)) })
  }

  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="text-sm font-medium">Símbolos</legend>
      <p className="text-sm text-muted">
        Declare cada símbolo do enunciado. Para grandezas sem dimensão, a unidade é 1.
      </p>
      <ul className="flex flex-col gap-4">
        {rows.map((row, index) => {
          const called = row.name.trim() === '' ? `símbolo ${index + 1}` : row.name.trim()
          return (
            <li key={row.id} className="border border-rule bg-surface p-3">
              <div
                role="group"
                aria-label={`Símbolo ${index + 1}`}
                className="grid grid-cols-2 items-end gap-3 md:grid-cols-6"
              >
                <TextField
                  label="Nome"
                  value={row.name}
                  monospace
                  onChange={(name) => {
                    change(row.id, { name })
                  }}
                />
                <SelectField
                  label="Papel"
                  value={row.role}
                  placeholder="escolha"
                  options={termOptions(vocabulary.symbol_roles)}
                  onChange={(role) => {
                    change(row.id, { role })
                  }}
                />
                <SelectField
                  label="Domínio"
                  value={row.domain}
                  placeholder="escolha"
                  options={termOptions(vocabulary.symbol_domains)}
                  onChange={(domain) => {
                    change(row.id, { domain })
                  }}
                />
                <TextField
                  label="Unidade"
                  value={row.unit}
                  monospace
                  onChange={(unit) => {
                    change(row.id, { unit })
                  }}
                />
                {takesArgument(row) ? (
                  <TextField
                    label="Argumento"
                    value={row.argument}
                    monospace
                    onChange={(argument) => {
                      change(row.id, { argument })
                    }}
                  />
                ) : null}
                {takesValue(row, symbolsCarryValues) ? (
                  <TextField
                    label="Valor"
                    value={row.value}
                    inputMode="decimal"
                    monospace
                    onChange={(value) => {
                      change(row.id, { value })
                    }}
                  />
                ) : null}
                <button
                  type="button"
                  aria-label={`Remover ${called}`}
                  disabled={rows.length === 1}
                  onClick={() => {
                    commit({ ...table, rows: rows.filter((item) => item.id !== row.id) })
                  }}
                  className={`${secondaryButton} justify-self-start px-3`}
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </button>
              </div>
            </li>
          )
        })}
      </ul>
      {error === undefined ? null : <p className="text-sm text-signal">{error}</p>}
      <div>
        <button
          type="button"
          onClick={() => {
            commit(withBlankRow(table))
          }}
          className={secondaryButton}
        >
          <Plus className="size-4" aria-hidden="true" />
          Adicionar símbolo
        </button>
      </div>
    </fieldset>
  )
}
