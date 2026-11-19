const INSTANT = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'medium' })
const PLAIN_FROM = 1e-3
const PLAIN_BELOW = 1e6
const PLAIN_DIGITS = 7
const EXPONENT_DIGITS = 6
const SHORT_IDENTIFIER_LENGTH = 8
const KIBIBYTE = 1024

export function formatInstant(iso: string): string {
  const instant = new Date(iso)
  return Number.isNaN(instant.getTime()) ? iso : INSTANT.format(instant)
}

export function formatSample(value: number): string {
  if (value === 0) return '0'
  const magnitude = Math.abs(value)
  if (magnitude >= PLAIN_FROM && magnitude < PLAIN_BELOW) {
    return String(Number(value.toPrecision(PLAIN_DIGITS)))
  }
  return value.toExponential(EXPONENT_DIGITS)
}

export function shortIdentifier(identifier: string): string {
  return identifier.slice(0, SHORT_IDENTIFIER_LENGTH)
}

export function formatMemory(bytes: number): string {
  if (bytes < KIBIBYTE) return `${bytes} B`
  if (bytes < KIBIBYTE ** 2) return `${(bytes / KIBIBYTE).toFixed(1)} KiB`
  return `${(bytes / KIBIBYTE ** 2).toFixed(1)} MiB`
}
