import type { Draft, DraftPath } from '@/features/editor/input-document'

export type DraftFieldProps = {
  draft: Draft
  onChange: (path: DraftPath, value: unknown) => void
}

export function pointerOf(path: DraftPath): string {
  return path.map((segment) => `/${segment.replaceAll('~', '~0').replaceAll('/', '~1')}`).join('')
}
