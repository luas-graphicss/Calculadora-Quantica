import { RunView } from '@/features/results/run-view'
import { useRunDetails } from '@/shared/api/queries'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { usePageTitle } from '@/shared/hooks/use-page-title'

type Props = {
  identifier: string
}

export function RunPage({ identifier }: Props) {
  const details = useRunDetails(identifier)
  usePageTitle(details.data?.run.card.title ?? 'Execução')

  if (details.data === undefined) {
    return details.error === undefined ? (
      <LoadingLine label="Carregando a execução" />
    ) : (
      <ErrorNotice error={details.error} />
    )
  }
  return <RunView details={details.data} />
}
