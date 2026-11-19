import { useRef, useState } from 'react'
import { useSWRConfig } from 'swr'

import { submitRun } from '@/shared/api/client'
import { describeError } from '@/shared/api/http'
import { RUNS_KEY } from '@/shared/api/queries'
import type { RunDetails } from '@/shared/api/schemas/run'
import { secondaryButton } from '@/shared/components/button-styles'
import { Notice } from '@/shared/components/notice'
import { navigate } from '@/shared/routing/use-route'

type Props = {
  details: RunDetails
  label: string
}

export function ResubmitButton({ details, label }: Props) {
  const idempotencyKey = useRef<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [problem, setProblem] = useState<string>()
  const { mutate } = useSWRConfig()

  async function resubmit() {
    idempotencyKey.current ??= crypto.randomUUID()
    setIsSubmitting(true)
    setProblem(undefined)
    try {
      const submitted = await submitRun({
        text: details.input.text,
        idempotencyKey: idempotencyKey.current,
        timeLimit: details.run.wall_seconds,
        parent: details.run.identifier,
      })
      if (submitted.kind === 'rejection') {
        const reasons = submitted.rejection.diagnostics.map((diagnostic) => diagnostic.message)
        setProblem(`Esta instalação não aceitou a entrada: ${reasons.join(' ')}`)
        return
      }
      await mutate(RUNS_KEY)
      navigate({ name: 'run', identifier: submitted.run.identifier })
    } catch (error) {
      setProblem(describeError(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={() => {
            void resubmit()
          }}
          className={secondaryButton}
        >
          {isSubmitting ? 'Enviando…' : label}
        </button>
      </div>
      {problem === undefined ? null : <Notice tone="problem">{problem}</Notice>}
    </div>
  )
}
