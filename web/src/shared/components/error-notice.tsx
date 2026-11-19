import { describeError } from '@/shared/api/http'
import { Notice } from '@/shared/components/notice'

type Props = {
  error: unknown
  title?: string
}

export function ErrorNotice({ error, title }: Props) {
  return (
    <Notice tone="problem" title={title}>
      {describeError(error)}
    </Notice>
  )
}
