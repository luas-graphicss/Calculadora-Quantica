import {
  auditScreen,
  NARROW,
  overflowingScreens,
  publishReport,
  type ScreenAudit,
  violationsOf,
} from './support/accessibility'
import {
  calculate,
  checkInterpretation,
  confirmAndCalculate,
  describeElectronWell,
  inputReview,
  loadInputFile,
  openForm,
} from './support/editor'
import { expect, test } from './support/fixtures'
import { CARDS, INPUTS } from './support/inputs'
import { answer, expectVerified, runHeading } from './support/results'
import { enter, openHistory } from './support/session'

const ENERGY = /^E = 0\.3760301621 eV$/

test('meets WCAG 2.2 AA on every screen, in a wide and in a narrow window', async ({
  page,
  bench,
}, testInfo) => {
  const audits: ScreenAudit[] = []
  const audit = async (screen: string) => {
    audits.push(...(await auditScreen(page, screen)))
  }

  await page.goto(bench.origin)
  await expect(page.getByRole('heading', { level: 1, name: 'Sessão não aberta' })).toBeVisible()
  await audit('sessão não aberta')

  await enter(page, bench)
  await audit('catálogo de problemas')

  await openForm(page, CARDS.wellEnergy)
  await audit('formulário da ficha')

  await checkInterpretation(page)
  const review = inputReview(page)
  await expect(review.getByRole('heading', { name: 'A entrada não foi aceita' })).toBeVisible()
  await audit('entrada recusada')

  await describeElectronWell(page, '1')
  await checkInterpretation(page)
  await expect(review.getByRole('heading', { name: 'Interpretação' })).toBeVisible()
  await audit('interpretação conferida')

  await confirmAndCalculate(page)
  await expectVerified(page, 'aprovada')
  await audit('resultado com uma grandeza')

  await page.getByRole('link', { name: 'Alterar e recalcular' }).click()
  await page.getByLabel('Valor de L').fill('2')
  await calculate(page)
  await expectVerified(page, 'aprovada')
  await page.getByRole('link', { name: 'Comparar com a execução de origem' }).click()
  await expect(page.getByRole('table', { name: 'Respostas das duas execuções' })).toBeVisible()
  await audit('comparação de execuções')

  await openForm(page, CARDS.discreteSpectrum)
  await loadInputFile(page, INPUTS.discreteSpectrum)
  await calculate(page)
  await expectVerified(page, 'aprovada')
  await expect(
    page.getByRole('region', { name: 'Tabelas e séries' }).getByRole('img'),
  ).not.toHaveCount(0)
  await audit('resultado com tabelas e séries')

  await openHistory(page)
  await audit('histórico')

  await publishReport(testInfo, audits)
  expect(violationsOf(audits), 'WCAG violations').toEqual([])
  expect(overflowingScreens(audits), 'screens that scroll sideways').toEqual([])
})

test('gives assistive technology the quantity, the unit and the state of a result in words', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await openForm(page, CARDS.wellEnergy)
  await describeElectronWell(page, '1')
  await calculate(page)
  await expectVerified(page, 'aprovada')

  const shown = answer(page)
  await expect(shown).toMatchAriaSnapshot(`
    - region "Resposta":
      - heading "Resposta" [level=2]
      - paragraph: energia do nível
      - paragraph: E = 0.3760301621 eV
      - paragraph:
        - text: "Expressão usada:"
        - math
        - text: "(em texto: E_n = h**2*n**2/(8*L**2*m))"
      - combobox "Unidade de exibição"
      - paragraph: A conversão usa o valor guardado. O cálculo não é refeito.
  `)
  await expect(shown.getByLabel('Unidade de exibição')).toHaveAccessibleDescription(
    'A conversão usa o valor guardado. O cálculo não é refeito.',
  )
  await expect(runHeading(page).getByText('concluída', { exact: true })).toBeVisible()
  await expect(runHeading(page).getByText('verificação aprovada', { exact: true })).toBeVisible()

  await page.setViewportSize({ width: NARROW.width, height: NARROW.height })
  await shown.getByText(ENERGY).scrollIntoViewIfNeeded()
  await expect(shown.getByText(ENERGY)).toBeInViewport({ ratio: 1 })
  await expect(runHeading(page).getByText('verificação aprovada', { exact: true })).toBeVisible()
})
