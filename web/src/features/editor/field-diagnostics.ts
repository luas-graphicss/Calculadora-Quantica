import { createContext, useContext } from 'react'

import type { Diagnostic } from '@/shared/api/schemas/diagnostics'

const NO_DIAGNOSTICS: readonly Diagnostic[] = []

export const FieldDiagnostics = createContext<readonly Diagnostic[]>(NO_DIAGNOSTICS)

export function useFieldError(pointer: string): string | undefined {
  const messages = useContext(FieldDiagnostics)
    .filter((diagnostic) => diagnostic.pointer === pointer)
    .map((diagnostic) => diagnostic.message)
  return messages.length === 0 ? undefined : messages.join(' ')
}
