import { CardEditor } from '@/features/editor/card-editor'
import { draftCard, parseDraft } from '@/features/editor/input-document'
import { useRunDetails } from '@/shared/api/queries'
import type { Catalog, CatalogChoice, CatalogQuestion } from '@/shared/api/schemas/catalog'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { Notice } from '@/shared/components/notice'

type Props = {
  catalog: Catalog
  question: CatalogQuestion
  choice: CatalogChoice
  from: string
}

export function DerivedEditor({ catalog, question, choice, from }: Props) {
  const source = useRunDetails(from)
  if (source.data === undefined) {
    return source.error === undefined ? (
      <LoadingLine label="Carregando a execução de origem" />
    ) : (
      <ErrorNotice error={source.error} />
    )
  }
  const parsed = parseDraft(source.data.input.text)
  if (!parsed.ok || draftCard(parsed.draft) !== choice.card.identifier) {
    return (
      <Notice tone="problem">
        A entrada da execução de origem não pertence a esta ficha e não pôde ser carregada no
        formulário.
      </Notice>
    )
  }
  return (
    <CardEditor
      key={`${choice.card.identifier}:${from}`}
      catalog={catalog}
      question={question}
      choice={choice}
      initialDraft={parsed.draft}
      parent={from}
    />
  )
}
