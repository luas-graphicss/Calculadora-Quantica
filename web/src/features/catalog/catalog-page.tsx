import { QuestionBlock } from '@/features/catalog/question-block'
import { useCatalog } from '@/shared/api/queries'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { PageHeading } from '@/shared/components/page-heading'
import { usePageTitle } from '@/shared/hooks/use-page-title'

export function CatalogPage() {
  usePageTitle('Problemas')
  const catalog = useCatalog()

  return (
    <div className="flex flex-col gap-8">
      <PageHeading title="Problemas">
        {catalog.data === undefined ? null : (
          <p className="text-sm text-muted">{`Catálogo ${catalog.data.version}`}</p>
        )}
      </PageHeading>
      {catalog.error === undefined ? null : <ErrorNotice error={catalog.error} />}
      {catalog.data === undefined && catalog.error === undefined ? (
        <LoadingLine label="Carregando o catálogo" />
      ) : null}
      {catalog.data?.questions.map((question) => (
        <QuestionBlock key={question.identifier} question={question} />
      ))}
    </div>
  )
}
