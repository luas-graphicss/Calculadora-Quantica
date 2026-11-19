import { textLink } from '@/shared/components/button-styles'
import { PageHeading } from '@/shared/components/page-heading'
import { usePageTitle } from '@/shared/hooks/use-page-title'
import { RouteLink } from '@/shared/routing/route-link'

export function NotFoundPage() {
  usePageTitle('Endereço desconhecido')
  return (
    <div className="flex flex-col gap-4">
      <PageHeading title="Endereço desconhecido" />
      <p>
        {'Este endereço não corresponde a nenhuma tela. '}
        <RouteLink to={{ name: 'catalog' }} className={textLink}>
          Ver os problemas
        </RouteLink>
      </p>
    </div>
  )
}
