import { expect, type Locator, type Page } from '@playwright/test'

export const CALCULATION_TIMEOUT_MS = 150_000

const ENERGY_IN_ELECTRONVOLTS = /^E = \S+ eV$/

export function answer(page: Page): Locator {
  return page.getByRole('region', { name: 'Resposta', exact: true })
}

export function verification(page: Page): Locator {
  return page.getByRole('region', { name: 'Verificações' })
}

export function runHeading(page: Page): Locator {
  return page.getByRole('main').locator('header').first()
}

export async function expectState(page: Page, state: string): Promise<void> {
  const announced = page.getByRole('status').filter({ hasText: `Estado da execução: ${state}.` })
  await expect(announced).toBeVisible({ timeout: CALCULATION_TIMEOUT_MS })
  await expect(runHeading(page)).toContainText(state)
}

export async function expectVerified(page: Page, verdict: string): Promise<void> {
  await expectState(page, 'concluída')
  await expect(runHeading(page)).toContainText(`verificação ${verdict}`)
}

export async function energyInElectronvolts(page: Page): Promise<number> {
  const shown = await answer(page).getByText(ENERGY_IN_ELECTRONVOLTS).innerText()
  return Number(shown.split(' ')[2])
}
