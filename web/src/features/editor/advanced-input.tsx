import { FileJson } from 'lucide-react'
import { useState } from 'react'

import { type Draft, draftCard, parseDraft } from '@/features/editor/input-document'
import { inputControl, secondaryButton } from '@/shared/components/button-styles'
import { Notice } from '@/shared/components/notice'
import { TextField } from '@/shared/components/text-field'

type Props = {
  text: string
  card: string
  timeLimit: string
  maxSeconds: number
  isTimeLimitValid: boolean
  onTimeLimitChange: (value: string) => void
  onReplace: (draft: Draft) => void
}

const MAX_FILE_BYTES = 1_048_576
const EDITOR_ROWS = 16

export function AdvancedInput({
  text,
  card,
  timeLimit,
  maxSeconds,
  isTimeLimitValid,
  onTimeLimitChange,
  onReplace,
}: Props) {
  const [edited, setEdited] = useState<string | null>(null)
  const [problem, setProblem] = useState<string>()

  function apply(source: string) {
    const parsed = parseDraft(source)
    if (!parsed.ok) {
      setProblem(parsed.message)
      return
    }
    const described = draftCard(parsed.draft)
    if (described !== card) {
      setProblem(
        `A entrada descreve a ficha ${described ?? 'não informada'}; este formulário é da ficha ${card}. ` +
          'Abra a ficha certa pela lista de problemas.',
      )
      return
    }
    setProblem(undefined)
    setEdited(null)
    onReplace(parsed.draft)
  }

  async function load(file: File) {
    if (file.size > MAX_FILE_BYTES) {
      setProblem('O arquivo passa de 1 MiB, o limite de uma entrada.')
      return
    }
    apply(await file.text())
  }

  return (
    <details className="border-t border-rule pt-5">
      <summary className="cursor-pointer text-base font-semibold">Opções avançadas</summary>
      <div className="flex flex-col gap-5 pt-4">
        <div className="grid grid-cols-1 md:grid-cols-3">
          <TextField
            label="Limite de tempo do cálculo, em segundos"
            value={timeLimit}
            inputMode="decimal"
            monospace
            hint={`Até ${maxSeconds} s.`}
            error={
              isTimeLimitValid ? undefined : `Informe um número maior que 0 e até ${maxSeconds}.`
            }
            onChange={onTimeLimitChange}
          />
        </div>
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-medium">Entrada em JSON</h3>
          {edited === null ? (
            <pre className="max-h-80 overflow-auto border border-rule bg-surface p-3 font-mono text-sm">
              {text}
            </pre>
          ) : (
            <textarea
              value={edited}
              rows={EDITOR_ROWS}
              aria-label="Entrada em JSON"
              autoComplete="off"
              autoCapitalize="off"
              spellCheck={false}
              onChange={(event) => {
                setEdited(event.target.value)
              }}
              className={`${inputControl} font-mono`}
            />
          )}
          {problem === undefined ? null : <Notice tone="problem">{problem}</Notice>}
          <div className="flex flex-wrap gap-3">
            {edited === null ? (
              <button
                type="button"
                onClick={() => {
                  setEdited(text)
                }}
                className={secondaryButton}
              >
                Editar em JSON
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => {
                    apply(edited)
                  }}
                  className={secondaryButton}
                >
                  Aplicar ao formulário
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEdited(null)
                    setProblem(undefined)
                  }}
                  className={secondaryButton}
                >
                  Descartar edição
                </button>
              </>
            )}
            <label
              className={`${secondaryButton} cursor-pointer focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-primary`}
            >
              <FileJson className="size-4" aria-hidden="true" />
              Carregar arquivo de entrada
              <input
                type="file"
                accept=".json,application/json"
                className="sr-only"
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  event.target.value = ''
                  if (file !== undefined) void load(file)
                }}
              />
            </label>
          </div>
        </div>
      </div>
    </details>
  )
}
