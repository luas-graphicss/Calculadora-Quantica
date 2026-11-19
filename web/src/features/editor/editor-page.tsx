import { CardEditor } from '@/features/editor/card-editor'
import { DerivedEditor } from '@/features/editor/derived-editor'
import { emptyDraft } from '@/features/editor/input-document'
import { useCatalog } from '@/shared/api/queries'
import { findChoice } from '@/shared/api/schemas/catalog'
import { textLink } from '@/shared/components/button-styles'
import { ErrorNotice } from '@/shared/components/error-notice'
import { LoadingLine } from '@/shared/components/loading-line'
import { Notice } from '@/shared/components/notice'
import { usePageTitle } from '@/shared/hooks/use-page-title'
import { RouteLink } from '@/shared/routing/route-link'

type Props = {
  card: string
  from: string | null
}

export function EditorPage({ card, from }: Props) {
  const catalog = useCatalog()
  const found = catalog.data === undefined ? undefined : findChoice(catalog.data, card)
  usePageTitle(found?.choice.card.title ?? 'Formular problema')

  if (catalog.data === undefined) {
    return catalog.error === undefined ? (
      <LoadingLine label="Carregando o catálogo" />
    ) : (
      <ErrorNotice error={catalog.error} />
    )
  }
  if (found === undefined) {
    return (
      <div className="flex flex-col gap-4">
        <Notice tone="problem">{`A ficha ${card} não está no catálogo desta instalação.`}</Notice>
        <p>
          <RouteLink to={{ name: 'catalog' }} className={textLink}>
            Ver os problemas disponíveis
          </RouteLink>
        </p>
      </div>
    )
  }
  if (from !== null) {
    return (
      <DerivedEditor
        catalog={catalog.data}
        question={found.question}
        choice={found.choice}
        from={from}
      />
    )
  }
  return (
    <CardEditor
      key={card}
      catalog={catalog.data}
      question={found.question}
      choice={found.choice}
      initialDraft={emptyDraft(card, found.choice.form)}
      parent={null}
    />
  )
}
