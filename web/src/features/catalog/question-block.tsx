import { useId } from 'react'

import type { CatalogQuestion } from '@/shared/api/schemas/catalog'
import { secondaryButton } from '@/shared/components/button-styles'
import { describeNature } from '@/shared/format/labels'
import { RouteLink } from '@/shared/routing/route-link'

type Props = {
  question: CatalogQuestion
}

export function QuestionBlock({ question }: Props) {
  const headingId = useId()
  return (
    <section
      aria-labelledby={headingId}
      className="grid grid-cols-1 gap-4 border-t border-rule pt-6 md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] md:gap-10"
    >
      <div className="flex flex-col gap-2">
        <h2 id={headingId} className="text-xl leading-snug font-semibold text-balance">
          {question.question}
        </h2>
        <p className="text-sm text-pretty text-muted">{question.context}</p>
      </div>
      <ul className="flex flex-col">
        {question.choices.map((choice) => (
          <li
            key={choice.card.identifier}
            className="flex flex-col gap-3 border-b border-rule py-4 first:pt-0 last:border-b-0 last:pb-0 md:flex-row md:items-start md:justify-between md:gap-6"
          >
            <div className="flex min-w-0 flex-col gap-1">
              <p className="text-pretty">{choice.answer}</p>
              <p className="text-sm text-muted">
                {`${choice.card.title}. Resposta ${describeNature(choice.card.method.nature)}.`}
              </p>
            </div>
            <RouteLink
              to={{ name: 'editor', card: choice.card.identifier, from: null }}
              className={`${secondaryButton} shrink-0`}
            >
              Formular
              <span className="sr-only">{`: ${choice.card.title}`}</span>
            </RouteLink>
          </li>
        ))}
      </ul>
    </section>
  )
}
