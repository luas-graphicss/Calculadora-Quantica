import { ResubmitButton } from '@/features/results/resubmit-button'
import type { RunOutcome } from '@/features/results/run-outcome'
import type { RunDetails } from '@/shared/api/schemas/run'
import { Notice } from '@/shared/components/notice'
import { DiagnosticList } from '@/shared/record/diagnostic-list'

type Props = {
  details: RunDetails
  outcome: Exclude<RunOutcome, { kind: 'record' }>
}

const NOTHING_KEPT = 'Não há resultado, e nenhum valor parcial é mostrado.'

export function EndedWithoutResult({ details, outcome }: Props) {
  const { state } = details.run
  return (
    <div className="flex flex-col gap-4">
      {state === 'cancelled' ? (
        <Notice tone="information" title="Cálculo cancelado">
          {NOTHING_KEPT}
        </Notice>
      ) : null}
      {state === 'interrupted' ? (
        <Notice tone="problem" title="Cálculo interrompido">
          {`A bancada foi encerrada antes do fim deste cálculo. ${NOTHING_KEPT}`}
        </Notice>
      ) : null}
      {outcome.kind === 'failure' ? (
        <Notice tone="problem" title="O cálculo terminou sem resultado">
          {outcome.message}
        </Notice>
      ) : null}
      {outcome.kind === 'rejection' ? (
        <>
          <h2 className="text-lg font-semibold">O cálculo terminou sem resultado</h2>
          <DiagnosticList diagnostics={outcome.rejection.diagnostics} />
        </>
      ) : null}
      {outcome.kind === 'unreadable' ? (
        <Notice tone="problem" title="Registro em formato desconhecido">
          Esta versão da interface não lê o formato deste registro. A entrada original e os hashes
          continuam disponíveis abaixo, e o pacote pode ser exportado.
        </Notice>
      ) : null}
      {outcome.kind === 'rejection' || outcome.kind === 'unreadable' ? null : (
        <ResubmitButton details={details} label="Calcular de novo" />
      )}
    </div>
  )
}
