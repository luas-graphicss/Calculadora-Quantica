import { type DraftFieldProps, pointerOf } from '@/features/editor/fields/draft-field'
import { ExpressionList } from '@/features/editor/fields/expression-list'
import { SymbolTable } from '@/features/editor/fields/symbol-table'
import { useFieldError } from '@/features/editor/field-diagnostics'
import { optionalText, textAt } from '@/features/editor/input-document'
import type {
  NotationFields as NotationDescription,
  Vocabulary,
} from '@/shared/api/schemas/catalog'
import { FieldGroup } from '@/shared/components/field-group'
import { SelectField } from '@/shared/components/select-field'
import { TextAreaField } from '@/shared/components/text-area-field'
import { TextField } from '@/shared/components/text-field'
import { describeTerm } from '@/shared/format/labels'

type Props = DraftFieldProps & {
  notation: NotationDescription
  vocabulary: Vocabulary
}

const STATEMENT_HINT =
  "Exemplos em texto: y' = -k*y, diff(x^2*sin(x), x), integral(sin(x), x, 0, pi)."

export function NotationFields({ notation, vocabulary, draft, onChange }: Props) {
  const notationError = useFieldError('/notation')
  const statementError = useFieldError(pointerOf(['statement']))
  const candidateError = useFieldError(pointerOf(['candidate']))

  return (
    <FieldGroup legend="Enunciado">
      <div className="grid grid-cols-1 md:grid-cols-3">
        <SelectField
          label="Notação"
          value={textAt(draft, ['notation'])}
          error={notationError}
          options={vocabulary.notations.map((item) => ({ value: item, label: describeTerm(item) }))}
          onChange={(chosen) => {
            onChange(['notation'], optionalText(chosen))
          }}
        />
      </div>
      {notation.has_statement ? (
        <TextAreaField
          label="Equação ou expressão"
          value={textAt(draft, ['statement'])}
          rows={2}
          hint={STATEMENT_HINT}
          error={statementError}
          onChange={(text) => {
            onChange(['statement'], optionalText(text))
          }}
        />
      ) : null}
      {notation.has_equations ? (
        <ExpressionList
          section="equations"
          legend="Equações"
          itemName="Equação"
          hint="Uma equação de primeira ordem por função incógnita, como y' = -k*y."
          draft={draft}
          onChange={onChange}
        />
      ) : null}
      {notation.has_conditions ? (
        <ExpressionList
          section="conditions"
          legend="Condições iniciais"
          itemName="Condição"
          hint="Uma condição por linha, como y(0) = y_0."
          draft={draft}
          onChange={onChange}
        />
      ) : null}
      {notation.has_candidate ? (
        <TextField
          label="Solução candidata"
          value={textAt(draft, ['candidate'])}
          monospace
          hint="A função que você quer conferir, como y(t) = y_0*exp(-k*t)."
          error={candidateError}
          onChange={(text) => {
            onChange(['candidate'], optionalText(text))
          }}
        />
      ) : null}
      <SymbolTable
        vocabulary={vocabulary}
        symbolsCarryValues={notation.symbols_carry_values}
        draft={draft}
        onChange={onChange}
      />
    </FieldGroup>
  )
}
