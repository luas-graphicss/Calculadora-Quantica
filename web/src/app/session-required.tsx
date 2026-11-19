import { PageHeading } from '@/shared/components/page-heading'
import { usePageTitle } from '@/shared/hooks/use-page-title'

export function SessionRequired() {
  usePageTitle('Sessão não aberta')
  return (
    <div className="flex max-w-prose flex-col gap-4">
      <PageHeading title="Sessão não aberta" />
      <p className="text-pretty">
        A bancada só mostra cálculos para a sessão aberta pelo arquivo de acesso. Abra no navegador
        o arquivo que o comando <code className="font-mono">qcalc serve</code> indica no terminal.
      </p>
      <p className="text-sm text-pretty text-muted">
        Se a bancada foi reiniciada, o arquivo de acesso mudou: use o novo.
      </p>
    </div>
  )
}
