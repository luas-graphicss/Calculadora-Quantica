import { Plus, Trash2 } from 'lucide-react'
import { useId, useRef, useState } from 'react'

import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { readPath } from '@/features/editor/input-document'
import { inputControl, secondaryButton } from '@/shared/components/button-styles'

type Props = DraftFieldProps & {
  section: 'equations' | 'conditions'
  legend: string
  itemName: string
  hint: string
}

type Row = {
  id: number
  text: string
}

function initialRows(stored: unknown): Row[] {
  const texts = Array.isArray(stored) ? stored.filter((item) => typeof item === 'string') : []
  return (texts.length === 0 ? [''] : texts).map((text, id) => ({ id, text }))
}

export function ExpressionList({ section, legend, itemName, hint, draft, onChange }: Props) {
  const [rows, setRows] = useState(() => initialRows(readPath(draft, [section])))
  const nextId = useRef(rows.length)
  const hintId = useId()
  const error = useFieldError(pointerOf([section]))

  function commit(updated: Row[]) {
    setRows(updated)
    const texts = updated.map((row) => row.text).filter((text) => text.trim() !== '')
    onChange([section], texts.length === 0 ? undefined : texts)
  }

  function addRow() {
    commit([...rows, { id: nextId.current, text: '' }])
    nextId.current += 1
  }

  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="text-sm font-medium">{legend}</legend>
      <p id={hintId} className="text-sm text-muted">
        {hint}
      </p>
      <ul className="flex flex-col gap-2">
        {rows.map((row, index) => (
          <li key={row.id} className="flex items-start gap-2">
            <input
              type="text"
              value={row.text}
              aria-label={`${itemName} ${index + 1}`}
              aria-describedby={hintId}
              autoComplete="off"
              autoCapitalize="off"
              spellCheck={false}
              onChange={(event) => {
                commit(
                  rows.map((item) =>
                    item.id === row.id ? { ...item, text: event.target.value } : item,
                  ),
                )
              }}
              className={`${inputControl} font-mono`}
            />
            <button
              type="button"
              aria-label={`Remover ${itemName.toLowerCase()} ${index + 1}`}
              disabled={rows.length === 1}
              onClick={() => {
                commit(rows.filter((item) => item.id !== row.id))
              }}
              className={`${secondaryButton} px-3`}
            >
              <Trash2 className="size-4" aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>
      {error === undefined ? null : <p className="text-sm text-signal">{error}</p>}
      <div>
        <button type="button" onClick={addRow} className={secondaryButton}>
          <Plus className="size-4" aria-hidden="true" />
          {`Adicionar ${itemName.toLowerCase()}`}
        </button>
      </div>
    </fieldset>
  )
}
