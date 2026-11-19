import { writeFile } from 'node:fs/promises'

import { AxeBuilder } from '@axe-core/playwright'
import type { Page, TestInfo } from '@playwright/test'

type Viewport = {
  name: string
  width: number
  height: number
}

export type ScreenAudit = {
  screen: string
  viewport: string
  engine: string
  rules_passed: number
  needing_manual_review: { rule: string; elements: number; reasons: string[] }[]
  violations: { rule: string; impact: string; help: string; elements: string[] }[]
  horizontal_overflow_px: number
}

const STANDARD = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] as const

const WIDE: Viewport = { name: 'janela larga, 1280 x 720', width: 1280, height: 720 }
export const NARROW: Viewport = { name: 'janela estreita, 320 x 640', width: 320, height: 640 }

const VIEWPORTS: readonly Viewport[] = [WIDE, NARROW]
const REPORT_FILE = process.env.QCALC_ACCESSIBILITY_REPORT
const REPORT_NAME = 'accessibility_report.json'

function horizontalOverflow(page: Page): Promise<number> {
  return page.evaluate(() => {
    const root = document.documentElement
    return root.scrollWidth - root.clientWidth
  })
}

export async function auditScreen(page: Page, screen: string): Promise<ScreenAudit[]> {
  const audits: ScreenAudit[] = []
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height })
    const found = await new AxeBuilder({ page }).withTags([...STANDARD]).analyze()
    audits.push({
      screen,
      viewport: viewport.name,
      engine: `${found.testEngine.name} ${found.testEngine.version}`,
      rules_passed: found.passes.length,
      needing_manual_review: found.incomplete.map((rule) => ({
        rule: rule.id,
        elements: rule.nodes.length,
        reasons: [
          ...new Set(rule.nodes.flatMap((node) => node.any.map((check) => check.message))),
        ].sort(),
      })),
      violations: found.violations.map((violation) => ({
        rule: violation.id,
        impact: violation.impact ?? 'unknown',
        help: violation.help,
        elements: violation.nodes.map((node) => node.target.join(' ')),
      })),
      horizontal_overflow_px: await horizontalOverflow(page),
    })
  }
  await page.setViewportSize({ width: WIDE.width, height: WIDE.height })
  return audits
}

export function violationsOf(audits: readonly ScreenAudit[]): string[] {
  return audits.flatMap((audit) =>
    audit.violations.map((violation) => `${audit.screen}, ${audit.viewport}: ${violation.rule}`),
  )
}

export function overflowingScreens(audits: readonly ScreenAudit[]): string[] {
  return audits
    .filter((audit) => audit.horizontal_overflow_px > 0)
    .map((audit) => `${audit.screen}, ${audit.viewport}: ${audit.horizontal_overflow_px} px`)
}

export async function publishReport(
  testInfo: TestInfo,
  audits: readonly ScreenAudit[],
): Promise<void> {
  const report = `${JSON.stringify(
    { document: 'accessibility_report', standard: STANDARD, audits },
    null,
    2,
  )}\n`
  await testInfo.attach(REPORT_NAME, { body: report, contentType: 'application/json' })
  if (REPORT_FILE !== undefined) await writeFile(REPORT_FILE, report)
}
