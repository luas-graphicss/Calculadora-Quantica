import {
  Ban,
  CircleAlert,
  CircleCheck,
  CircleHelp,
  CircleX,
  Clock,
  LoaderCircle,
  type LucideIcon,
  Unplug,
} from 'lucide-react'

import type { RunState } from '@/shared/api/schemas/run'

export type Tone = 'positive' | 'neutral' | 'negative'

export type StatusDescription = {
  label: string
  tone: Tone
  icon: LucideIcon
}

const VERIFICATION = new Map<string, StatusDescription>([
  ['passed', { label: 'aprovada', tone: 'positive', icon: CircleCheck }],
  ['conditional', { label: 'condicional', tone: 'neutral', icon: CircleAlert }],
  ['inconclusive', { label: 'inconclusiva', tone: 'neutral', icon: CircleHelp }],
  ['failed', { label: 'reprovada', tone: 'negative', icon: CircleX }],
])

const RUN_STATE = {
  queued: { label: 'na fila', tone: 'neutral', icon: Clock },
  running: { label: 'calculando', tone: 'neutral', icon: LoaderCircle },
  succeeded: { label: 'concluída', tone: 'positive', icon: CircleCheck },
  failed: { label: 'sem resultado', tone: 'negative', icon: CircleX },
  cancelled: { label: 'cancelada', tone: 'neutral', icon: Ban },
  interrupted: { label: 'interrompida', tone: 'negative', icon: Unplug },
} as const satisfies Record<RunState, StatusDescription>

const CHECK_KIND = new Map([
  ['proof', 'demonstração'],
  ['numerical_evidence', 'evidência numérica'],
  ['consistency_test', 'teste de consistência'],
])

const NATURE = new Map([
  ['exact', 'exata'],
  ['approximate', 'aproximada'],
])

const VOCABULARY = new Map([
  ['text', 'texto'],
  ['latex', 'LaTeX'],
  ['variable', 'variável'],
  ['parameter', 'parâmetro'],
  ['function', 'função'],
  ['real', 'real'],
  ['positive', 'positivo'],
  ['negative', 'negativo'],
  ['nonnegative', 'não negativo'],
  ['nonzero', 'não nulo'],
  ['independent', 'incertezas independentes'],
  ['local', 'local'],
  ['imported', 'importada'],
])

const DIMENSIONLESS = '1'

export function describeVerification(status: string): StatusDescription {
  return VERIFICATION.get(status) ?? { label: status, tone: 'neutral', icon: CircleHelp }
}

export function describeRunState(state: RunState): StatusDescription {
  return RUN_STATE[state]
}

export function describeCheckKind(kind: string): string {
  return CHECK_KIND.get(kind) ?? kind
}

export function describeNature(nature: string): string {
  return NATURE.get(nature) ?? nature
}

export function describeTerm(term: string): string {
  return VOCABULARY.get(term) ?? term
}

export function unitLabel(unit: string): string {
  return unit === DIMENSIONLESS ? 'adimensional' : unit
}

export function withUnit(value: string, unit: string): string {
  return unit === DIMENSIONLESS ? value : `${value} ${unit}`
}
