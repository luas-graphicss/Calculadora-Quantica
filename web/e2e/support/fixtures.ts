import { expect, test as base } from '@playwright/test'

import { Bench } from './bench'

type BenchFactory = {
  open: () => Promise<Bench>
}

type Fixtures = {
  benches: BenchFactory
  bench: Bench
}

const LOCAL_PROTOCOLS = new Set(['file:', 'data:', 'blob:', 'about:'])
const LOOPBACK = '127.0.0.1'

function staysOnThisMachine(address: string): boolean {
  const url = new URL(address)
  return (
    LOCAL_PROTOCOLS.has(url.protocol) || (url.protocol === 'http:' && url.hostname === LOOPBACK)
  )
}

export const test = base.extend<Fixtures>({
  benches: async ({}, use) => {
    const opened: Bench[] = []
    await use({
      open: async () => {
        const bench = await Bench.onEmptyProfile()
        opened.push(bench)
        return bench
      },
    })
    await Promise.all(opened.map((bench) => bench.remove()))
  },

  bench: async ({ benches }, use) => {
    await use(await benches.open())
  },

  page: async ({ page }, use) => {
    const sentOutside: string[] = []
    const uncaught: string[] = []
    page.context().on('request', (request) => {
      if (!staysOnThisMachine(request.url())) sentOutside.push(request.url())
    })
    page.on('pageerror', (error) => {
      uncaught.push(error.message)
    })

    await use(page)

    expect(sentOutside, 'requests sent outside this machine').toEqual([])
    expect(uncaught, 'uncaught errors in the interface').toEqual([])
  },
})

export { expect }
