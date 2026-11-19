import { useState } from 'react'

import { arrayText, parseArrayText } from '@/features/editor/array-text'
import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { optionalText, readPath, textAt } from '@/features/editor/input-document'
import type { ArrayField as ArrayDescription } from '@/shared/api/schemas/catalog'
import { CheckboxField } from '@/shared/components/checkbox-field'
import { TextAreaField } from '@/shared/components/text-area-field'
import { TextField } from '@/shared/components/text-field'

type Props = DraftFieldProps & {
  field: ArrayDescription
}

const VECTOR_HINT =
  'Lista entre colchetes, como [1, 1]. Uma entrada complexa é {"real": 0, "imaginary": 1}.'
const MATRIX_HINT =
  'Uma lista por linha, como [[1, 0], [0, -1]]. Uma entrada complexa é {"real": 0, "imaginary": 1}.'
const MATRIX_RANK = 2
const VECTOR_ROWS = 2
const MATRIX_ROWS = 5

export function ArrayField({ field, draft, onChange }: Props) {
  const path = field.member === null ? [field.section] : [field.section, field.member]
  const [text, setText] = useState(() => arrayText(readPath(draft, path), field.rank))
  const [syntaxError, setSyntaxError] = useState<string>()
  const valueError = useFieldError(pointerOf(path))
  const sectionError = useFieldError(pointerOf([field.section]))
  const unitError = useFieldError(pointerOf([field.section, 'unit']))
  const isMatrix = field.rank >= MATRIX_RANK
  const label = field.presence === 'optional' ? `${field.label} (opcional)` : field.label

  return (
    <div className="flex flex-col gap-3">
      <TextAreaField
        label={label}
        value={text}
        rows={isMatrix ? MATRIX_ROWS : VECTOR_ROWS}
        hint={isMatrix ? MATRIX_HINT : VECTOR_HINT}
        error={syntaxError ?? valueError ?? sectionError}
        onChange={(typed) => {
          setText(typed)
          const parsed = parseArrayText(typed)
          setSyntaxError(parsed.ok ? undefined : parsed.message)
          if (parsed.ok) onChange(path, parsed.value)
        }}
      />
      {field.has_unit ? (
        <div className="grid grid-cols-1 md:grid-cols-3">
          <TextField
            label={`Unidade de ${field.label}`}
            value={textAt(draft, [field.section, 'unit'])}
            monospace
            hint="Para um observável sem dimensão, a unidade é 1."
            error={unitError}
            onChange={(unit) => {
              onChange([field.section, 'unit'], optionalText(unit.trim()))
            }}
          />
        </div>
      ) : null}
      {field.is_normalizable ? (
        <CheckboxField
          label="Normalizar: dividir as amplitudes informadas pela norma antes de calcular"
          checked={readPath(draft, [field.section, 'normalize']) === true}
          onChange={(checked) => {
            onChange([field.section, 'normalize'], checked ? true : undefined)
          }}
        />
      ) : null}
    </div>
  )
}
