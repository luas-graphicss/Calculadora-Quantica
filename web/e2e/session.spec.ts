import { expect, test } from './support/fixtures'
import { enter } from './support/session'

const UNAUTHORIZED = 401

test('shows no calculation to a page that was not opened by the access file', async ({
  page,
  bench,
}) => {
  await page.goto(bench.origin)

  await expect(page.getByRole('heading', { level: 1, name: 'Sessão não aberta' })).toBeVisible()
  await expect(page.getByRole('main')).toContainText('qcalc serve')
  for (const resource of ['catalog', 'runs']) {
    const refused = await page.request.get(`${bench.origin}/api/v1/${resource}`)
    expect(refused.status(), resource).toBe(UNAUTHORIZED)
  }
})

test('keeps the session secret out of the address and out of the reach of scripts', async ({
  page,
  bench,
}) => {
  await enter(page, bench)

  expect(page.url()).toBe(`${bench.origin}/`)
  expect(await page.evaluate(() => document.cookie)).toBe('')
  const [session] = await page.context().cookies(`${bench.origin}/api/v1/session`)
  expect(session?.httpOnly).toBe(true)
  expect(session?.sameSite).toBe('Strict')
})
