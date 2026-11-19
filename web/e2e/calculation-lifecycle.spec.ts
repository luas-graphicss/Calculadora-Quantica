import type { Page } from '@playwright/test'

import {
  allowSeconds,
  calculate,
  checkInterpretation,
  chooseCard,
  confirmHypotheses,
  type DeclaredSymbol,
  declareSymbols,
  describeElectronWell,
  inputReview,
  loadInputFile,
  openForm,
  runIdentifier,
} from './support/editor'
import { expect, test } from './support/fixtures'
import { CARDS, INPUTS } from './support/inputs'
import { answer, expectState, expectVerified, runHeading, verification } from './support/results'
import { enter, openHistory, recordedRuns } from './support/session'

const GENEROUS_SECONDS = 300
const NO_PARTIAL_VALUE = 'Não há resultado, e nenhum valor parcial é mostrado.'
const LOST_RESPONSE = 'Não foi possível falar com a bancada.'
const FORCED_RATE_SYMBOLS: readonly DeclaredSymbol[] = [
  { name: 't', role: 'variável', domain: 'real', unit: 's' },
  { name: 'a', role: 'parâmetro', domain: 'real', unit: '1/s' },
  { name: 's', role: 'parâmetro', domain: 'real', unit: '1/s' },
  { name: 'y', role: 'função', domain: 'real', unit: '1', argument: 't' },
]

async function startLongCalculation(page: Page): Promise<string> {
  await openForm(page, CARDS.timeEvolution)
  await loadInputFile(page, INPUTS.longEvolution)
  await allowSeconds(page, GENEROUS_SECONDS)
  const identifier = await calculate(page)
  await expectState(page, 'calculando')
  return identifier
}

async function calculateWellEnergy(page: Page): Promise<void> {
  await openForm(page, CARDS.wellEnergy)
  await describeElectronWell(page, '1')
  await calculate(page)
  await expectVerified(page, 'aprovada')
}

test('cancels a long calculation, frees its process and calculates again', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await startLongCalculation(page)
  await expect.poll(() => bench.calculationProcesses()).toHaveLength(1)

  await page.getByRole('button', { name: 'Cancelar cálculo' }).click()

  await expectState(page, 'cancelada')
  await expect(page.getByRole('main')).toContainText(`Cálculo cancelado${NO_PARTIAL_VALUE}`)
  await expect(answer(page)).toHaveCount(0)
  await expect(runHeading(page)).not.toContainText('verificação')
  await expect.poll(() => bench.calculationProcesses()).toHaveLength(0)

  await calculateWellEnergy(page)
  await openHistory(page)
  await expect(recordedRuns(page)).toHaveCount(2)
  await expect(recordedRuns(page).nth(1)).toContainText('cancelada')
})

test('brings back as interrupted, never as verified, a calculation cut by the end of the bench', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await calculateWellEnergy(page)
  const interrupted = await startLongCalculation(page)

  await bench.kill()
  await bench.start()
  await enter(page, bench)

  await page.goto(`${bench.origin}/#/execucoes/${interrupted}`)
  await expectState(page, 'interrompida')
  await expect(page.getByRole('alert')).toContainText('Cálculo interrompido')
  await expect(page.getByRole('alert')).toContainText(NO_PARTIAL_VALUE)
  await expect(answer(page)).toHaveCount(0)
  await expect(runHeading(page)).not.toContainText('verificação')
  await expect(page.getByRole('button', { name: 'Calcular de novo' })).toBeVisible()

  await openHistory(page)
  await expect(recordedRuns(page)).toHaveCount(2)
  await expect(recordedRuns(page).nth(0)).toContainText('interrompida')
  await expect(recordedRuns(page).nth(1)).toContainText('E = 0.3760301621 eV')
  await expect(recordedRuns(page).nth(1)).toContainText('aprovada')
})

test('ends without a result the calculation whose process is killed and keeps the bench working', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await startLongCalculation(page)
  await expect.poll(() => bench.calculationProcesses()).toHaveLength(1)
  const [calculation] = await bench.calculationProcesses()
  if (calculation === undefined) throw new Error('The calculation process was not found')

  process.kill(calculation, 'SIGKILL')

  await expectState(page, 'sem resultado')
  await expect(
    page.getByRole('heading', { name: 'O cálculo terminou sem resultado' }),
  ).toBeVisible()
  await expect(page.getByRole('main')).toContainText('nenhum resultado parcial foi aproveitado')
  await expect(answer(page)).toHaveCount(0)
  await expect(runHeading(page)).not.toContainText('verificação')

  await calculateWellEnergy(page)
})

test('does not create a second run when a submission is repeated after a lost response', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await openForm(page, CARDS.wellEnergy)
  await describeElectronWell(page, '1')
  await checkInterpretation(page)

  let responsesLost = 0
  await page.route('**/api/v1/runs?*', async (route) => {
    if (route.request().method() !== 'POST' || responsesLost > 0) {
      await route.fallback()
      return
    }
    responsesLost += 1
    await route.fetch()
    await route.abort('connectionreset')
  })

  const confirm = page.getByRole('button', { name: 'Confirmar e calcular' })
  await confirm.click()
  await expect(inputReview(page).getByRole('alert')).toContainText(LOST_RESPONSE)
  expect(responsesLost).toBe(1)

  await confirm.click()
  await page.waitForURL(/#\/execucoes\//)
  await expectVerified(page, 'aprovada')
  const repeated = runIdentifier(page)

  await openHistory(page)
  await expect(recordedRuns(page)).toHaveCount(1)
  await expect(recordedRuns(page).getByRole('link')).toHaveAttribute(
    'href',
    `#/execucoes/${repeated}`,
  )
})

test('points each invalid value at its field and accepts the corrected input', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await chooseCard(page, CARDS.wellEnergy)
  await confirmHypotheses(page)
  await page.getByLabel('Valor de m').fill('-1')
  await page.getByLabel('Unidade de m').selectOption('kg')
  await page.getByLabel('Valor de L').fill('1')
  await page.getByLabel('Unidade de L').selectOption('nm')
  await page.getByLabel('índice do nível (n)').fill('0')
  await page.getByLabel('Unidade de energia do nível').selectOption('eV')

  await checkInterpretation(page)

  const review = inputReview(page)
  await expect(review).toBeFocused()
  await expect(review.getByRole('heading', { name: 'A entrada não foi aceita' })).toBeVisible()
  const problems = review.getByRole('listitem')
  await expect(problems).toHaveCount(2)
  await expect(problems.nth(0)).toContainText('grandezas › massa da partícula (m) › valor')
  await expect(problems.nth(0)).toContainText('valor maior que zero')
  await expect(problems.nth(1)).toContainText('grandezas › índice do nível (n)')

  const mass = page.getByLabel('Valor de m')
  const level = page.getByLabel('índice do nível (n)')
  await expect(mass).toHaveAttribute('aria-invalid', 'true')
  await expect(mass).toHaveAccessibleDescription(/deve ser estritamente positivo/)
  await expect(level).toHaveAttribute('aria-invalid', 'true')
  await expect(level).toHaveAccessibleDescription(/deve ser um inteiro positivo/)
  await expect(page.getByRole('button', { name: 'Confirmar e calcular' })).toHaveCount(0)

  await mass.fill('9.1093837139e-31')
  await level.fill('1')
  await expect(review).toContainText('A entrada mudou depois da última conferência.')
  await checkInterpretation(page)

  await expect(review.getByRole('heading', { name: 'Interpretação' })).toBeVisible()
  await expect(mass).not.toHaveAttribute('aria-invalid', 'true')
  await expect(page.getByRole('button', { name: 'Confirmar e calcular' })).toBeVisible()
})

test('reports an under-resolved mesh as inconclusive, never as converged', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await openForm(page, CARDS.discreteSpectrum)
  await loadInputFile(page, INPUTS.coarseSpectrum)
  await calculate(page)

  await expectVerified(page, 'inconclusiva')
  const verdict = answer(page).getByRole('status')
  await expect(verdict).toContainText(
    'A verificação não chegou a uma conclusão sobre este resultado',
  )
  await expect(verdict).toContainText('a malha não está no regime assintótico')
  await expect(
    verification(page).getByRole('listitem').filter({ hasText: 'mesh_refinement' }),
  ).toContainText('inconclusiva')
})

test('states the condition under which a conditional answer holds', async ({ page, bench }) => {
  await enter(page, bench)
  await openForm(page, CARDS.generalSolution)
  await page.getByLabel('Equação ou expressão').fill("y' = a*y + s")
  await declareSymbols(page, FORCED_RATE_SYMBOLS)
  await calculate(page)

  await expectVerified(page, 'condicional')
  const verdict = answer(page).getByRole('status')
  await expect(verdict).toContainText('Este resultado vale sob condição')
  await expect(verdict).toContainText(
    'hipótese que o domínio declarado dos parâmetros não confirma',
  )
  const problem = page.getByRole('region', { name: 'Problema e hipóteses' })
  await expect(problem.getByRole('heading', { name: 'A resposta supõe' })).toBeVisible()
  await expect(problem.getByRole('heading', { name: 'Casos especiais' })).toBeVisible()
  await expect(problem).toContainText('se a = 0: y(t) = C + s*t')
})
