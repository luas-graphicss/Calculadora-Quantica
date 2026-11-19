import { defineConfig, devices } from '@playwright/test'

const TEST_TIMEOUT_MS = 240_000
const ASSERTION_TIMEOUT_MS = 15_000
const CONCURRENT_BENCHES = 2

export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results',
  fullyParallel: true,
  forbidOnly: process.env.CI !== undefined,
  retries: 0,
  workers: CONCURRENT_BENCHES,
  timeout: TEST_TIMEOUT_MS,
  expect: { timeout: ASSERTION_TIMEOUT_MS },
  reporter: [
    ['list'],
    ['junit', { outputFile: 'test-results/end-to-end.xml' }],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    ...devices['Desktop Chrome'],
    locale: 'pt-BR',
    timezoneId: 'America/Sao_Paulo',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
})
