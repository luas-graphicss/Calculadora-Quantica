import { readFile } from 'node:fs/promises'

import { expect, type Locator, type Page } from '@playwright/test'

import type { Card } from './inputs'

export type DeclaredSymbol = {
  name: string
  role: 'variável' | 'parâmetro' | 'função'
  domain: 'real' | 'positivo'
  unit: string
  argument?: string
}

const RUN_LOCATION = /#\/execucoes\/([0-9a-f]{32})$/
const ELECTRON_MASS = 'massa do elétron (m_e), constante do catálogo'

export async function chooseCard(page: Page, card: Card): Promise<void> {
  await page.getByRole('link', { name: card.title }).click()
  await expect(page.getByRole('heading', { level: 1, name: card.title })).toBeVisible()
}

export async function openForm(page: Page, card: Card): Promise<void> {
  await page.goto(`${new URL(page.url()).origin}/#/formular/${card.identifier}`)
  await expect(page.getByRole('heading', { level: 1, name: card.title })).toBeVisible()
}

export async function confirmHypotheses(page: Page): Promise<void> {
  const hypotheses = page.getByRole('group', { name: 'Hipóteses do modelo' }).getByRole('checkbox')
  for (const hypothesis of await hypotheses.all()) {
    await hypothesis.check()
  }
}

export async function describeElectronWell(page: Page, width: string): Promise<void> {
  await confirmHypotheses(page)
  await page.getByLabel('Origem de m').selectOption({ label: ELECTRON_MASS })
  await page.getByLabel('Valor de L').fill(width)
  await page.getByLabel('Unidade de L').selectOption('nm')
  await page.getByLabel('índice do nível (n)').fill('1')
  await page.getByLabel('Unidade de energia do nível').selectOption('eV')
}

export async function declareSymbols(
  page: Page,
  symbols: readonly DeclaredSymbol[],
): Promise<void> {
  for (const [index, symbol] of symbols.entries()) {
    if (index > 0) await page.getByRole('button', { name: 'Adicionar símbolo' }).click()
    const row = page.getByRole('group', { name: `Símbolo ${index + 1}`, exact: true })
    await row.getByLabel('Nome').fill(symbol.name)
    await row.getByLabel('Papel').selectOption({ label: symbol.role })
    await row.getByLabel('Domínio').selectOption({ label: symbol.domain })
    await row.getByLabel('Unidade').fill(symbol.unit)
    if (symbol.argument !== undefined) await row.getByLabel('Argumento').fill(symbol.argument)
  }
}

export async function loadInputFile(page: Page, file: string): Promise<void> {
  const described: unknown = JSON.parse(await readFile(file, 'utf8'))
  const description =
    typeof described === 'object' && described !== null && 'description' in described
      ? String(described.description)
      : ''
  await page.getByText('Opções avançadas', { exact: true }).click()
  await page.getByLabel('Carregar arquivo de entrada').setInputFiles(file)
  await expect(page.getByLabel('Descrição do problema (opcional)')).toHaveValue(description)
}

export async function allowSeconds(page: Page, seconds: number): Promise<void> {
  await page.getByLabel('Limite de tempo do cálculo, em segundos').fill(String(seconds))
}

export function inputReview(page: Page): Locator {
  return page.getByRole('region', { name: 'Conferência da entrada' })
}

export async function checkInterpretation(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Conferir interpretação' }).click()
}

export function runIdentifier(page: Page): string {
  const identifier = RUN_LOCATION.exec(page.url())?.[1]
  if (identifier === undefined) throw new Error(`${page.url()} is not the page of a run`)
  return identifier
}

export async function confirmAndCalculate(page: Page): Promise<string> {
  await page.getByRole('button', { name: 'Confirmar e calcular' }).click()
  await page.waitForURL(RUN_LOCATION)
  return runIdentifier(page)
}

export async function calculate(page: Page): Promise<string> {
  await checkInterpretation(page)
  return confirmAndCalculate(page)
}
