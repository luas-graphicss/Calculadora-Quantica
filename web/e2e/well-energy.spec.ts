import {
  checkInterpretation,
  chooseCard,
  confirmAndCalculate,
  describeElectronWell,
  inputReview,
} from './support/editor'
import { expect, test } from './support/fixtures'
import { CARDS } from './support/inputs'
import { answer, energyInElectronvolts, expectVerified } from './support/results'
import { enter, openHistory, recordedRuns } from './support/session'

const ENERGY_AT_ONE_NANOMETRE = 'E = 0.3760301621 eV'
const ENERGY_AT_TWO_NANOMETRES = 'E = 0.09400754053 eV'
const QUARTER = 0.25
const RATIO_DIGITS = 9

test('solves the well, widens it from 1 nm to 2 nm and keeps both results', async ({
  page,
  bench,
}) => {
  const submissions: string[] = []
  page.on('request', (request) => {
    const isSubmission =
      request.method() === 'POST' && new URL(request.url()).pathname === '/api/v1/runs'
    if (isSubmission) submissions.push(request.url())
  })
  await enter(page, bench)

  await chooseCard(page, CARDS.wellEnergy)
  await describeElectronWell(page, '1')
  await checkInterpretation(page)

  const review = inputReview(page)
  await expect(review).toBeFocused()
  await expect(review.getByRole('heading', { name: 'Interpretação' })).toBeVisible()
  await expect(review).toContainText('Nada foi calculado ainda.')
  await expect(review.getByRole('row', { name: 'L 1 nm 1E-9 m' })).toBeVisible()
  await expect(review).toContainText(
    'energia do nível (E), em eV, com 10 algarismos significativos.',
  )
  expect(submissions).toHaveLength(0)

  const narrowRun = await confirmAndCalculate(page)
  await expectVerified(page, 'aprovada')
  await expect(answer(page)).toContainText(ENERGY_AT_ONE_NANOMETRE)
  const narrowEnergy = await energyInElectronvolts(page)

  await answer(page).getByLabel('Unidade de exibição').selectOption('meV')
  await expect(answer(page)).toContainText('E = 376.0301621 meV')
  expect(submissions).toHaveLength(1)

  await page.getByRole('link', { name: 'Alterar e recalcular' }).click()
  await expect(page.getByLabel('Valor de L')).toHaveValue('1')
  await expect(page.getByRole('main')).toContainText(
    'O envio cria uma execução nova; a anterior continua no histórico.',
  )
  await page.getByLabel('Valor de L').fill('2')
  await checkInterpretation(page)
  const wideRun = await confirmAndCalculate(page)
  await expectVerified(page, 'aprovada')
  await expect(answer(page)).toContainText(ENERGY_AT_TWO_NANOMETRES)

  expect(wideRun).not.toBe(narrowRun)
  expect((await energyInElectronvolts(page)) / narrowEnergy).toBeCloseTo(QUARTER, RATIO_DIGITS)

  await page.getByRole('link', { name: 'Comparar com a execução de origem' }).click()
  await expect(
    page.getByRole('heading', { level: 1, name: 'Comparação de execuções' }),
  ).toBeVisible()
  await expect(
    page
      .getByRole('table', { name: 'Diferenças na entrada' })
      .getByRole('row', { name: 'grandezas › largura do poço (L) › valor 1 2' }),
  ).toBeVisible()
  const energies = page
    .getByRole('table', { name: 'Respostas das duas execuções' })
    .getByRole('row', { name: 'energia do nível (E)' })
    .getByRole('cell')
  await expect(energies).toHaveText([
    'energia do nível (E)',
    '0.3760301621 eV',
    '0.09400754053 eV',
    '0.25',
  ])

  await openHistory(page)
  await expect(recordedRuns(page)).toHaveCount(2)
  await expect(recordedRuns(page).nth(0)).toContainText(ENERGY_AT_TWO_NANOMETRES)
  await expect(recordedRuns(page).nth(1)).toContainText(ENERGY_AT_ONE_NANOMETRE)
  expect(submissions).toHaveLength(2)
})

test('shows the recorded value in another unit without calculating again', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await chooseCard(page, CARDS.wellEnergy)
  await describeElectronWell(page, '1')
  await checkInterpretation(page)
  await confirmAndCalculate(page)
  await expectVerified(page, 'aprovada')

  const unit = answer(page).getByLabel('Unidade de exibição')
  await unit.selectOption('J')
  await expect(answer(page)).toContainText('E = 6.024667394E-20 J')
  await expect(answer(page)).toContainText(
    'A conversão usa o valor guardado. O cálculo não é refeito.',
  )
  await unit.selectOption({ label: 'como foi registrada' })
  await expect(answer(page)).toContainText(ENERGY_AT_ONE_NANOMETRE)

  await openHistory(page)
  await expect(recordedRuns(page)).toHaveCount(1)
})
