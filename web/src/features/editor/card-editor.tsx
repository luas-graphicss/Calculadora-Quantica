import { useEffect, useReducer, useRef } from 'react'
import { useSWRConfig } from 'swr'

import { AdvancedInput } from '@/features/editor/advanced-input'
import { CardFormFields } from '@/features/editor/card-form-fields'
import { editorReducer, initialEditorState, parseTimeLimit } from '@/features/editor/editor-state'
import { FieldDiagnostics } from '@/features/editor/field-diagnostics'
import { type Draft, type DraftPath, serializeDraft } from '@/features/editor/input-document'
import { InterpretationPanel } from '@/features/editor/interpretation-panel'
import { submitRun, validateInput } from '@/shared/api/client'
import { describeError } from '@/shared/api/http'
import { RUNS_KEY } from '@/shared/api/queries'
import type { Catalog, CatalogChoice, CatalogQuestion } from '@/shared/api/schemas/catalog'
import type { Diagnostic } from '@/shared/api/schemas/diagnostics'
import { primaryButton, secondaryButton, textLink } from '@/shared/components/button-styles'
import { Notice } from '@/shared/components/notice'
import { PageHeading } from '@/shared/components/page-heading'
import { shortIdentifier } from '@/shared/format/values'
import { DiagnosticList } from '@/shared/record/diagnostic-list'
import { RouteLink } from '@/shared/routing/route-link'
import { navigate } from '@/shared/routing/use-route'

type Props = {
  catalog: Catalog
  question: CatalogQuestion
  choice: CatalogChoice
  initialDraft: Draft
  parent: string | null
}

const NO_DIAGNOSTICS: readonly Diagnostic[] = []

export function CardEditor({ catalog, question, choice, initialDraft, parent }: Props) {
  const [state, dispatch] = useReducer(editorReducer, initialDraft, (draft) =>
    initialEditorState(draft, catalog.time_limit.default_seconds),
  )
  const outcome = useRef<HTMLElement>(null)
  const { mutate } = useSWRConfig()
  const { check, submission } = state
  const text = serializeDraft(state.draft)
  const timeLimit = parseTimeLimit(state.timeLimit, catalog.time_limit.max_seconds)
  const interpretation =
    check.status === 'interpreted' && check.text === text ? check.interpretation : null
  const rejection = check.status === 'rejected' && check.text === text ? check.rejection : null
  const isStale =
    (check.status === 'interpreted' || check.status === 'rejected') && check.text !== text
  const isBusy = check.status === 'checking' || submission.status === 'submitting'

  useEffect(() => {
    if (check.status === 'idle' || check.status === 'checking') return
    outcome.current?.focus()
  }, [check])

  function changeField(path: DraftPath, value: unknown) {
    dispatch({ type: 'field_changed', path, value })
  }

  async function checkInterpretation() {
    if (timeLimit === null) return
    dispatch({ type: 'check_started' })
    try {
      const validated = await validateInput(text, timeLimit)
      dispatch({
        type: 'check_finished',
        check:
          validated.kind === 'interpretation'
            ? { status: 'interpreted', text, interpretation: validated.interpretation }
            : { status: 'rejected', text, rejection: validated.rejection },
      })
    } catch (error) {
      dispatch({
        type: 'check_finished',
        check: { status: 'failed', message: describeError(error) },
      })
    }
  }

  async function submit() {
    if (interpretation === null || timeLimit === null) return
    const attempt =
      state.attempt?.text === text ? state.attempt : { text, key: crypto.randomUUID() }
    dispatch({ type: 'submission_started', attempt })
    try {
      const submitted = await submitRun({ text, idempotencyKey: attempt.key, timeLimit, parent })
      if (submitted.kind === 'rejection') {
        dispatch({
          type: 'check_finished',
          check: { status: 'rejected', text, rejection: submitted.rejection },
        })
        return
      }
      await mutate(RUNS_KEY)
      navigate({ name: 'run', identifier: submitted.run.identifier })
    } catch (error) {
      dispatch({ type: 'submission_failed', message: describeError(error) })
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeading eyebrow={question.question} title={choice.card.title}>
        <p className="max-w-prose text-sm text-pretty text-muted">{choice.answer}</p>
        {parent === null ? null : (
          <p className="text-sm">
            {'Derivada da execução '}
            <RouteLink to={{ name: 'run', identifier: parent }} className={textLink}>
              {shortIdentifier(parent)}
            </RouteLink>
            {'. O envio cria uma execução nova; a anterior continua no histórico.'}
          </p>
        )}
      </PageHeading>
      <form
        noValidate
        onSubmit={(event) => {
          event.preventDefault()
          void checkInterpretation()
        }}
        className="flex max-w-3xl flex-col gap-8"
      >
        <FieldDiagnostics value={rejection?.diagnostics ?? NO_DIAGNOSTICS}>
          <CardFormFields
            form={choice.form}
            catalog={catalog}
            revision={state.revision}
            draft={state.draft}
            onChange={changeField}
          />
        </FieldDiagnostics>
        <AdvancedInput
          text={text}
          card={choice.card.identifier}
          timeLimit={state.timeLimit}
          maxSeconds={catalog.time_limit.max_seconds}
          isTimeLimitValid={timeLimit !== null}
          onTimeLimitChange={(value) => {
            dispatch({ type: 'time_limit_changed', value })
          }}
          onReplace={(draft) => {
            dispatch({ type: 'draft_replaced', draft })
          }}
        />
        <div className="flex flex-wrap items-center gap-3 border-t border-ink pt-5">
          <button
            type="submit"
            disabled={isBusy || timeLimit === null}
            className={interpretation === null ? primaryButton : secondaryButton}
          >
            {check.status === 'checking' ? 'Conferindo…' : 'Conferir interpretação'}
          </button>
        </div>
      </form>
      <section
        ref={outcome}
        tabIndex={-1}
        aria-label="Conferência da entrada"
        className="flex max-w-3xl flex-col gap-5"
      >
        {check.status === 'failed' ? <Notice tone="problem">{check.message}</Notice> : null}
        {isStale ? (
          <Notice tone="information">
            A entrada mudou depois da última conferência. Confira de novo antes de calcular.
          </Notice>
        ) : null}
        {rejection === null ? null : (
          <>
            <h2 className="text-lg font-semibold">A entrada não foi aceita</h2>
            <DiagnosticList diagnostics={rejection.diagnostics} form={choice.form} />
          </>
        )}
        {interpretation === null ? null : (
          <>
            <h2 className="text-lg font-semibold">Interpretação</h2>
            <p className="text-sm text-muted">
              É assim que a calculadora leu a entrada. Nada foi calculado ainda.
            </p>
            <InterpretationPanel interpretation={interpretation} />
            {submission.status === 'failed' ? (
              <Notice tone="problem">{submission.message}</Notice>
            ) : null}
            <div>
              <button
                type="button"
                disabled={isBusy}
                onClick={() => {
                  void submit()
                }}
                className={primaryButton}
              >
                {submission.status === 'submitting' ? 'Enviando…' : 'Confirmar e calcular'}
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  )
}
