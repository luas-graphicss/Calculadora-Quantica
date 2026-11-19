import type { CardForm } from '@/shared/api/schemas/catalog'
import type { Diagnostic } from '@/shared/api/schemas/diagnostics'
import { describePointer } from '@/shared/format/pointers'

type Props = {
  diagnostics: readonly Diagnostic[]
  form?: CardForm
}

type ExcerptProps = {
  excerpt: NonNullable<Diagnostic['excerpt']>
}

function Excerpt({ excerpt }: ExcerptProps) {
  const { text, start, end } = excerpt
  const pointed = text.slice(start, end)
  return (
    <div className="flex flex-col gap-1">
      <code className="block overflow-x-auto border border-rule bg-surface px-3 py-2 font-mono text-sm whitespace-pre">
        {text.slice(0, start)}
        <mark>{pointed}</mark>
        {text.slice(end)}
      </code>
      <p className="text-sm text-muted">
        {`Trecho apontado: “${pointed}”, caracteres ${start + 1} a ${Math.max(end, start + 1)}.`}
      </p>
    </div>
  )
}

export function DiagnosticList({ diagnostics, form }: Props) {
  return (
    <ul className="flex flex-col gap-4">
      {diagnostics.map((diagnostic) => (
        <li
          key={`${diagnostic.pointer}:${diagnostic.code}:${diagnostic.message}`}
          className="flex flex-col gap-2 border border-signal bg-surface p-4"
        >
          <p className="font-medium text-pretty">{diagnostic.message}</p>
          <dl className="grid grid-cols-1 gap-x-4 gap-y-1 text-sm md:grid-cols-[6rem_1fr]">
            <dt className="text-muted">Onde</dt>
            <dd>{describePointer(diagnostic.pointer, form)}</dd>
            {diagnostic.expected === null ? null : (
              <>
                <dt className="text-muted">Esperado</dt>
                <dd>{diagnostic.expected}</dd>
              </>
            )}
          </dl>
          {diagnostic.excerpt === null ? null : <Excerpt excerpt={diagnostic.excerpt} />}
        </li>
      ))}
    </ul>
  )
}
