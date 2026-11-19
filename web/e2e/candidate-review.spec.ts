import { calculate, chooseCard, type DeclaredSymbol, declareSymbols } from './support/editor'
import { expect, test } from './support/fixtures'
import { CARDS } from './support/inputs'
import { answer, expectVerified, verification } from './support/results'
import { enter, openHistory, recordedRuns } from './support/session'

const DECAY_SYMBOLS: readonly DeclaredSymbol[] = [
  { name: 't', role: 'variável', domain: 'real', unit: 's' },
  { name: 'k', role: 'parâmetro', domain: 'positivo', unit: '1/s' },
  { name: 'y_0', role: 'parâmetro', domain: 'positivo', unit: '1' },
  { name: 'y', role: 'função', domain: 'real', unit: '1', argument: 't' },
]
const UNMET_CONDITION =
  'Checagem reprovada: A função informada assume o valor declarado no ponto da condição inicial.'

test('explains the unmet initial condition of a wrong candidate, then accepts the right one', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await chooseCard(page, CARDS.candidateReview)
  await page.getByLabel('Equação ou expressão').fill("y' = -k*y")
  await page.getByRole('textbox', { name: 'Condição 1' }).fill('y(0) = y_0')
  await page.getByLabel('Solução candidata').fill('y(t) = 2*y_0*exp(-k*t)')
  await declareSymbols(page, DECAY_SYMBOLS)

  await calculate(page)
  await expectVerified(page, 'reprovada')

  const verdict = answer(page).getByRole('alert')
  await expect(verdict).toContainText('A verificação reprovou este resultado')
  await expect(verdict).toContainText(UNMET_CONDITION)
  await expect(verdict).toContainText('Observado: o resíduo y_0 não se anula')

  const checks = verification(page).getByRole('listitem')
  await expect(checks.filter({ hasText: 'initial_condition' })).toContainText('reprovada')
  await expect(checks.filter({ hasText: 'equation_residual' })).toContainText('aprovada')
  await expect(checks.first()).toContainText('initial_condition')
  await expect(page.locator('details', { hasText: 'Entrada original' })).not.toHaveAttribute('open')

  await page.getByRole('link', { name: 'Alterar e recalcular' }).click()
  await expect(page.getByLabel('Solução candidata')).toHaveValue('y(t) = 2*y_0*exp(-k*t)')
  await page.getByLabel('Solução candidata').fill('y(t) = y_0*exp(-k*t)')
  await calculate(page)
  await expectVerified(page, 'aprovada')
  await expect(answer(page).getByRole('alert')).toHaveCount(0)

  await openHistory(page)
  await expect(recordedRuns(page)).toHaveCount(2)
  await expect(recordedRuns(page).nth(0)).toContainText('aprovada')
  await expect(recordedRuns(page).nth(1)).toContainText('reprovada')
})
