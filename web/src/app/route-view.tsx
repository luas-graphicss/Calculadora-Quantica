import { NotFoundPage } from '@/app/not-found-page'
import { CatalogPage } from '@/features/catalog/catalog-page'
import { EditorPage } from '@/features/editor/editor-page'
import { ComparisonPage } from '@/features/history/comparison-page'
import { HistoryPage } from '@/features/history/history-page'
import { RunPage } from '@/features/results/run-page'
import type { Route } from '@/shared/routing/routes'

type Props = {
  route: Route
}

export function RouteView({ route }: Props) {
  switch (route.name) {
    case 'catalog':
      return <CatalogPage />
    case 'editor':
      return <EditorPage card={route.card} from={route.from} />
    case 'run':
      return <RunPage key={route.identifier} identifier={route.identifier} />
    case 'history':
      return <HistoryPage />
    case 'comparison':
      return <ComparisonPage base={route.base} other={route.other} />
    case 'unknown':
      return <NotFoundPage />
  }
}
