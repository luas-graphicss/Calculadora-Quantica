import { inputReview } from './support/editor'
import { expect, test } from './support/fixtures'
import { CARDS } from './support/inputs'
import { activate, chooseOption, replaceWith, tabBackTo, tabTo, typeInto } from './support/keyboard'
import { manifestOf, savedPackage } from './support/packages'
import { answer, expectVerified } from './support/results'
import { enter } from './support/session'

const ELECTRON_MASS_IN_KILOGRAMS = '9.1093837139e-31'
const RUN_LOCATION = /#\/execucoes\/[0-9a-f]{32}$/

test('goes from the question to the exported package with the keyboard alone, reading and correcting an error on the way', async ({
  page,
  bench,
}, testInfo) => {
  await enter(page, bench)
  const main = page.getByRole('main')

  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: 'Ir para o conteúdo' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(main).toBeFocused()

  await activate(page, page.getByRole('link', { name: CARDS.wellEnergy.title }))
  await expect(page.getByRole('heading', { level: 1, name: CARDS.wellEnergy.title })).toBeVisible()
  await expect(main).toBeFocused()

  const hypotheses = page.getByRole('group', { name: 'Hipóteses do modelo' }).getByRole('checkbox')
  for (const hypothesis of await hypotheses.all()) {
    await tabTo(page, hypothesis)
    await page.keyboard.press('Space')
    await expect(hypothesis).toBeChecked()
  }
  const mass = page.getByLabel('Valor de m')
  await typeInto(page, mass, '-1')
  await chooseOption(page, page.getByLabel('Unidade de m'), 'kg')
  await typeInto(page, page.getByLabel('Valor de L'), '1')
  await chooseOption(page, page.getByLabel('Unidade de L'), 'nm')
  await typeInto(page, page.getByLabel('índice do nível (n)'), '1')
  await chooseOption(page, page.getByLabel('Unidade de energia do nível'), 'eV')
  const check = page.getByRole('button', { name: 'Conferir interpretação' })
  await activate(page, check)

  const review = inputReview(page)
  await expect(review).toBeFocused()
  await expect(review.getByRole('heading', { name: 'A entrada não foi aceita' })).toBeVisible()
  await expect(review.getByRole('listitem')).toHaveCount(1)
  await expect(review.getByRole('listitem')).toContainText(
    'grandezas › massa da partícula (m) › valor',
  )
  await expect(mass).toHaveAttribute('aria-invalid', 'true')
  await expect(mass).toHaveAccessibleDescription(/deve ser estritamente positivo/)

  await tabBackTo(page, mass)
  await replaceWith(page, ELECTRON_MASS_IN_KILOGRAMS)
  await activate(page, check)
  await expect(review.getByRole('heading', { name: 'Interpretação' })).toBeVisible()
  await expect(review).toBeFocused()

  await activate(page, page.getByRole('button', { name: 'Confirmar e calcular' }))
  await page.waitForURL(RUN_LOCATION)
  await expectVerified(page, 'aprovada')
  await expect(main).toBeFocused()
  await expect(answer(page)).toContainText('E = 0.3760301621 eV')

  await chooseOption(page, answer(page).getByLabel('Unidade de exibição'), 'meV')
  await expect(answer(page)).toContainText('E = 376.0301621 meV')

  await tabTo(page, page.getByRole('link', { name: 'Exportar pacote' }))
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.keyboard.press('Enter'),
  ])
  const files = await savedPackage(download, testInfo.outputPath('exported-by-keyboard.zip'))
  expect(manifestOf(files).files.map((file) => file.path)).toContain('outcome.json')
})
