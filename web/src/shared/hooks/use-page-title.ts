import { useEffect } from 'react'

const PRODUCT = 'Calculadora Quântica'

export function usePageTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} · ${PRODUCT}`
  }, [title])
}
