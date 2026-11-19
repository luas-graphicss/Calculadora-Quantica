const BASE =
  'inline-flex min-h-11 items-center justify-center gap-2 rounded-md border px-4 py-2 text-sm font-medium ' +
  'transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-60 md:min-h-9'

export const primaryButton = `${BASE} border-primary bg-primary text-on-primary hover:border-ink hover:bg-ink`

export const secondaryButton = `${BASE} border-rule-strong bg-surface text-ink hover:border-ink`

export const dangerButton = `${BASE} border-signal bg-surface text-signal hover:bg-signal hover:text-on-primary`

export const textLink = 'text-primary underline underline-offset-4 hover:text-ink'

export const inputControl =
  'min-h-11 w-full rounded-md border border-rule-strong bg-surface px-3 py-2 text-base text-ink ' +
  'aria-[invalid=true]:border-signal disabled:bg-paper disabled:text-muted md:min-h-9 md:text-sm'
