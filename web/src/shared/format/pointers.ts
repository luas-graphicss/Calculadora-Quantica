import type { CardForm } from '@/shared/api/schemas/catalog'

const SEPARATOR = ' › '

const SECTIONS = new Map([
  ['schema_version', 'versão do esquema'],
  ['problem', 'ficha'],
  ['description', 'descrição'],
  ['hypotheses', 'hipóteses'],
  ['parameters', 'grandezas'],
  ['notation', 'notação'],
  ['statement', 'enunciado'],
  ['symbols', 'símbolos'],
  ['equations', 'equações'],
  ['conditions', 'condições'],
  ['candidate', 'candidata'],
  ['numerics', 'resolução numérica'],
  ['requested', 'resposta pedida'],
  ['uncertainty', 'incerteza'],
])

const LEAVES = new Map([
  ['value', 'valor'],
  ['unit', 'unidade'],
  ['constant', 'constante'],
  ['quantity', 'grandeza'],
  ['significant_digits', 'algarismos significativos'],
  ['role', 'papel'],
  ['domain', 'domínio'],
  ['argument', 'argumento'],
  ['normalize', 'normalização'],
  ['covariance', 'covariância'],
  ['standard_uncertainties', 'incertezas padrão'],
])

const ITEMS = new Map([
  ['conditions', 'condição'],
  ['equations', 'equação'],
])

function decodeSegment(segment: string): string {
  return segment.replaceAll('~1', '/').replaceAll('~0', '~')
}

function namedLabel(section: string, name: string, form: CardForm | undefined): string | undefined {
  if (form === undefined) return undefined
  if (section === 'parameters' || section === 'standard_uncertainties') {
    const field = [...form.quantities, ...form.counts].find((item) => item.name === name)
    return field === undefined ? undefined : `${field.label} (${field.symbol})`
  }
  if (section === 'numerics') {
    return form.settings.find((item) => item.name === name)?.label
  }
  return undefined
}

function arrayLabel(section: string, form: CardForm | undefined): string | undefined {
  return form?.arrays.find((item) => item.section === section)?.label
}

export function describePointer(pointer: string, form?: CardForm): string {
  const segments = pointer
    .split('/')
    .filter((segment) => segment !== '')
    .map(decodeSegment)
  const [section, ...rest] = segments
  if (section === undefined) return 'a entrada inteira'
  const parts = [arrayLabel(section, form) ?? SECTIONS.get(section) ?? section]
  let context = section
  for (const segment of rest) {
    const item = ITEMS.get(context)
    const named = namedLabel(context, segment, form)
    if (item !== undefined && /^\d+$/.test(segment)) {
      parts.splice(-1, 1, `${item} ${Number(segment) + 1}`)
    } else if (named !== undefined) {
      parts.push(named)
    } else if (context === 'symbols') {
      parts.push(`símbolo ${segment}`)
    } else {
      parts.push(LEAVES.get(segment) ?? segment)
    }
    context = segment
  }
  return parts.join(SEPARATOR)
}
