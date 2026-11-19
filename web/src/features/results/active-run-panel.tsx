import { LoaderCircle } from 'lucide-react'
import { useState } from 'react'
import { useSWRConfig } from 'swr'

import { cancelRun } from '@/shared/api/client'
import { describeError } from '@/shared/api/http'
import { runKey, RUNS_KEY } from '@/shared/api/queries'
import type { Run } from '@/shared/api/schemas/run'
import { dangerButton } from '@/shared/components/button-styles'
import { Notice } from '@/shared/components/notice'

type Props = {
  run: Run
}

export function ActiveRunPanel({ run }: Props) {
  const [isCancelling, setIsCancelling] = useState(false)
  const [problem, setProblem] = useState<string>()
  const { mutate } = useSWRConfig()

  async function cancel() {
    setIsCancelling(true)
    setProblem(undefined)
    try {
      await cancelRun(run.identifier)
      await Promise.all([mutate(runKey(run.identifier)), mutate(RUNS_KEY)])
    } catch (error) {
      setProblem(describeError(error))
    } finally {
      setIsCancelling(false)
    }
  }

  return (
    <div className="flex flex-col gap-3 border border-rule-strong bg-surface p-4">
      <p className="flex items-center gap-2 font-medium">
        <LoaderCircle
          className="size-4 animate-spin motion-reduce:animate-none"
          aria-hidden="true"
        />
        {run.state === 'queued' ? 'Na fila de cálculo.' : 'Calculando.'}
      </p>
      <p className="text-sm text-muted">
        {`Limite de tempo: ${run.wall_seconds} s. Esta página se atualiza quando o cálculo termina.`}
      </p>
      <div>
        <button
          type="button"
          disabled={isCancelling}
          onClick={() => {
            void cancel()
          }}
          className={dangerButton}
        >
          {isCancelling ? 'Cancelando…' : 'Cancelar cálculo'}
        </button>
      </div>
      {problem === undefined ? null : <Notice tone="problem">{problem}</Notice>}
    </div>
  )
}
