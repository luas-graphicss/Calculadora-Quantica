import { calculate, loadInputFile, openForm } from './support/editor'
import { expect, test } from './support/fixtures'
import { CARDS, INPUTS } from './support/inputs'
import { answer, expectVerified } from './support/results'
import { enter } from './support/session'

const MESH_POINTS = 513
const SHOWN_ROWS = 200
const ENERGY_DIGITS = 8
const EXPECTED_LEVELS = [
  { symbol: 'E_1', energy: 0.3760289823 },
  { symbol: 'E_2', energy: 1.504101772 },
  { symbol: 'E_3', energy: 3.384175898 },
]

test('shows the spectrum as a table and the eigenfunctions as series with axes, units and the same data in a table', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await openForm(page, CARDS.discreteSpectrum)
  await loadInputFile(page, INPUTS.discreteSpectrum)
  await calculate(page)
  await expectVerified(page, 'aprovada')

  const spectrum = answer(page).getByRole('table', { name: 'Respostas' })
  await expect(spectrum.getByRole('columnheader')).toHaveText([
    'Grandeza',
    'Símbolo',
    'Valor',
    'Unidade',
    'Erro estimado',
  ])
  for (const level of EXPECTED_LEVELS) {
    const cells = spectrum.getByRole('row', { name: level.symbol }).getByRole('cell')
    expect(Number(await cells.nth(2).innerText())).toBeCloseTo(level.energy, ENERGY_DIGITS)
    await expect(cells.nth(3)).toHaveText('eV')
    await expect(cells.nth(4)).toHaveText(/^± 0\.0+\d+$/)
  }

  const eigenfunctions = page
    .getByRole('region', { name: 'Tabelas e séries' })
    .getByRole('article', { name: /^Autofunções normalizadas/ })
  const chart = eigenfunctions.getByRole('img')
  await expect(chart).toHaveAccessibleName(
    'Gráfico de psi_1(x), psi_2(x), psi_3(x), em m^-1/2, em função de x, em m. ' +
      'Os mesmos dados estão na tabela desta seção.',
  )
  await expect(chart.getByText('x (m)', { exact: true })).toBeVisible()
  await expect(chart.getByText('m^-1/2', { exact: true })).toBeVisible()
  await expect(chart.locator('polyline')).toHaveCount(EXPECTED_LEVELS.length)
  const drawn = await chart.locator('polyline').first().getAttribute('points')
  expect(drawn?.split(' ')).toHaveLength(MESH_POINTS)
  await expect(eigenfunctions.getByRole('listitem')).toHaveText([
    'psi_1(x)',
    'psi_2(x)',
    'psi_3(x)',
  ])

  await eigenfunctions.getByText('Dados em tabela').click()
  const samples = eigenfunctions.getByRole('table')
  await expect(samples.getByRole('columnheader')).toHaveText([
    'x (m)',
    'psi_1(x) (m^-1/2)',
    'psi_2(x) (m^-1/2)',
    'psi_3(x) (m^-1/2)',
  ])
  await expect(samples.locator('tbody').getByRole('row')).toHaveCount(SHOWN_ROWS)
  await expect(eigenfunctions).toContainText(
    `A tabela mostra as primeiras ${SHOWN_ROWS} de ${MESH_POINTS} linhas. O arquivo CSV traz todas.`,
  )

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    eigenfunctions.getByRole('link', { name: /^Baixar CSV com unidades/ }).click(),
  ])
  const stream = await download.createReadStream()
  const lines = (await new Response(stream as unknown as ReadableStream).text())
    .trimEnd()
    .split('\r\n')
  expect(lines[0]).toBe('x [m],psi_1(x) [m^-1/2],psi_2(x) [m^-1/2],psi_3(x) [m^-1/2]')
  expect(lines).toHaveLength(MESH_POINTS + 1)
})

test('draws the probability density with its own unit, apart from amplitudes and phases', async ({
  page,
  bench,
}) => {
  await enter(page, bench)
  await openForm(page, CARDS.timeEvolution)
  await loadInputFile(page, INPUTS.beatEvolution)
  await calculate(page)
  await expectVerified(page, 'aprovada')

  const series = page.getByRole('region', { name: 'Tabelas e séries' })
  const density = series.getByRole('article', {
    name: 'Densidade de probabilidade no instante final',
  })
  await expect(density.getByRole('img')).toHaveCount(1)
  await expect(density.getByRole('img')).toHaveAccessibleName(
    /^Gráfico de \|psi\(x\)\|\^2, em 1\/m, em função de x, em m\./,
  )

  const observables = series
    .getByRole('article', { name: 'Observáveis nos instantes salvos' })
    .getByRole('img')
  await expect(observables).toHaveCount(2)
  await expect(observables.nth(0)).toHaveAccessibleName(
    /^Gráfico de \|\|psi\|\|, \|c_1\|\^2, \|c_2\|\^2, em adimensional, em função de t, em s\./,
  )
  await expect(observables.nth(1)).toHaveAccessibleName(
    /^Gráfico de phi, phi exata dos modos discretos, em rad, em função de t, em s\./,
  )
})
