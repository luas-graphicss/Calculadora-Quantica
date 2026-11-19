import { expect, type Page } from '@playwright/test'

import type { Bench } from './bench'

export async function enter(page: Page, bench: Bench): Promise<void> {
  await page.goto(bench.launchUrl)
  await page.waitForURL(`${bench.origin}/`)
  await expect(page.getByRole('heading', { level: 1, name: 'Problemas' })).toBeVisible()
}

export async function openHistory(page: Page): Promise<void> {
  await page
    .getByRole('navigation', { name: 'Seções' })
    .getByRole('link', { name: 'Histórico' })
    .click()
  await expect(page.getByRole('heading', { level: 1, name: 'Histórico' })).toBeVisible()
}

export function recordedRuns(page: Page) {
  return page
    .getByRole('table', { name: /^Execuções registradas/ })
    .locator('tbody')
    .getByRole('row')
}
