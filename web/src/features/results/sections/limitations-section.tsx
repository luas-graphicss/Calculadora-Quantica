import { SectionBlock } from '@/shared/components/section-block'

type Props = {
  limitations: readonly string[]
}

export function LimitationsSection({ limitations }: Props) {
  return (
    <SectionBlock title="Limitações">
      <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
        {limitations.map((limitation) => (
          <li key={limitation} className="text-pretty">
            {limitation}
          </li>
        ))}
      </ul>
    </SectionBlock>
  )
}
