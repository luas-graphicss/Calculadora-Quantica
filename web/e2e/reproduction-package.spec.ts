import { writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'

import type { Page } from '@playwright/test'

import { printedDocument } from './support/command-line'
import { calculate, chooseCard, describeElectronWell, runIdentifier } from './support/editor'
import { expect, test } from './support/fixtures'
import { CARDS } from './support/inputs'
import {
  exportPackage,
  importPackage,
  manifestOf,
  type PackageFiles,
  sha256,
  textOf,
  withManifest,
  withText,
  writePackage,
} from './support/packages'
import { answer, expectState, expectVerified, runHeading } from './support/results'
import { enter, openHistory, recordedRuns } from './support/session'

const RECORDED_ENERGY = 'E = 0.3760301621 eV'
const EARLIER_VERSION = '0.1.0'
const PACKAGED_FILES = [
  'answers.csv',
  'input.json',
  'manifest.json',
  'outcome.json',
  'problem.json',
]

async function calculateWellEnergy(page: Page): Promise<void> {
  await chooseCard(page, CARDS.wellEnergy)
  await describeElectronWell(page, '1')
  await calculate(page)
  await expectVerified(page, 'aprovada')
}

async function reexecute(page: Page): Promise<void> {
  const imported = runIdentifier(page)
  await page.getByRole('button', { name: 'Reexecutar nesta instalação' }).click()
  await expect(page).not.toHaveURL(new RegExp(`${imported}$`))
  await expectVerified(page, 'aprovada')
}

function withoutKeys(document: Record<string, unknown>, ...keys: string[]): object {
  return Object.fromEntries(Object.entries(document).filter(([key]) => !keys.includes(key)))
}

function parsed(files: PackageFiles, name: string): Record<string, unknown> {
  return JSON.parse(textOf(files, name)) as Record<string, unknown>
}

test('reproduces on an empty profile the package exported by another bench', async ({
  page,
  bench,
  benches,
}, testInfo) => {
  await enter(page, bench)
  await calculateWellEnergy(page)
  const exported = testInfo.outputPath('exported.zip')
  const files = await exportPackage(page, exported)

  expect(Object.keys(files).sort()).toEqual(PACKAGED_FILES)
  for (const listed of manifestOf(files).files) {
    expect(sha256(files[listed.path] ?? new Uint8Array()), listed.path).toBe(listed.sha256)
  }
  expect(textOf(files, 'answers.csv')).toContain(',0.3760301621,eV,')
  for (const name of PACKAGED_FILES) {
    expect(textOf(files, name), name).not.toContain(bench.dataDirectory)
    expect(textOf(files, name), name).not.toContain(homedir())
  }

  const emptyProfile = await benches.open()
  await enter(page, emptyProfile)
  await openHistory(page)
  await expect(page.getByRole('main')).toContainText('Nenhuma execução registrada.')
  await importPackage(page, exported)

  await expectState(page, 'concluída')
  await expect(runHeading(page)).toContainText('importada')
  await expect(page.getByRole('main')).toContainText('Nada foi recalculado nesta instalação.')
  await expect(answer(page)).toContainText(RECORDED_ENERGY)
  expect(await emptyProfile.calculationProcesses()).toEqual([])

  await openHistory(page)
  await expect(recordedRuns(page)).toHaveCount(1)
  await expect(recordedRuns(page)).toContainText('importada')

  await recordedRuns(page).getByRole('link').click()
  await reexecute(page)
  await expect(answer(page)).toContainText(RECORDED_ENERGY)
  await expect(runHeading(page)).not.toContainText('importada')

  await page.getByRole('link', { name: 'Comparar com a execução de origem' }).click()
  await expect(page.getByRole('region', { name: 'Versões' })).toContainText(
    'As duas execuções registram as mesmas versões',
  )
  await expect(
    page.getByRole('region', { name: 'Diferenças na entrada', exact: true }),
  ).toContainText('As duas entradas são iguais.')
  await expect(
    page
      .getByRole('table', { name: 'Respostas das duas execuções' })
      .getByRole('row', { name: 'energia do nível (E)' })
      .getByRole('cell')
      .last(),
  ).toHaveText('1')
})

test('refuses a package with an altered artifact before calculating anything', async ({
  page,
  bench,
  benches,
}, testInfo) => {
  await enter(page, bench)
  await calculateWellEnergy(page)
  const files = await exportPackage(page, testInfo.outputPath('exported.zip'))
  const answers = textOf(files, 'answers.csv')
  const altered = testInfo.outputPath('altered.zip')
  await writePackage(
    altered,
    withText(files, 'answers.csv', answers.replace('0.3760301621', '0.3760301622')),
  )

  const emptyProfile = await benches.open()
  await enter(page, emptyProfile)
  await openHistory(page)
  await importPackage(page, altered)

  const refusal = page.getByRole('alert')
  await expect(refusal).toContainText('O pacote não foi importado')
  await expect(refusal).toContainText(
    'o arquivo answers.csv não confere com o hash declarado no manifesto',
  )
  await expect(refusal).toContainText('Nada foi importado nem calculado.')
  await expect(page.getByRole('main')).toContainText('Nenhuma execução registrada.')
  expect(await emptyProfile.calculationProcesses()).toEqual([])
})

test('shows the version divergence of an imported package before the answers', async ({
  page,
  bench,
  benches,
}, testInfo) => {
  await enter(page, bench)
  await calculateWellEnergy(page)
  const files = await exportPackage(page, testInfo.outputPath('exported.zip'))
  const manifest = manifestOf(files)
  const fromEarlierVersion = testInfo.outputPath('earlier-version.zip')
  await writePackage(
    fromEarlierVersion,
    withManifest(files, {
      ...manifest,
      generator: { ...manifest.generator, version: EARLIER_VERSION },
      run: { ...manifest.run, package_version: EARLIER_VERSION },
    }),
  )

  const emptyProfile = await benches.open()
  await enter(page, emptyProfile)
  await openHistory(page)
  await importPackage(page, fromEarlierVersion)
  await expectState(page, 'concluída')
  await reexecute(page)
  await page.getByRole('link', { name: 'Comparar com a execução de origem' }).click()

  const versions = page.getByRole('region', { name: 'Versões' })
  await expect(versions.getByRole('alert')).toContainText('As execuções usaram versões diferentes')
  const divergence = versions.getByRole('row', { name: 'calculadora' }).getByRole('cell')
  await expect(divergence.nth(1)).toHaveText(EARLIER_VERSION)
  await expect(divergence.nth(2)).not.toHaveText(EARLIER_VERSION)

  const answers = page.getByRole('region', { name: 'Respostas', exact: true })
  const versionsBox = await versions.boundingBox()
  const answersBox = await answers.boundingBox()
  expect(versionsBox?.y ?? Number.POSITIVE_INFINITY).toBeLessThan(answersBox?.y ?? 0)
})

test('records through the interface what the command line prints for the same input', async ({
  page,
  bench,
}, testInfo) => {
  await enter(page, bench)
  await calculateWellEnergy(page)
  const files = await exportPackage(page, testInfo.outputPath('exported.zip'))
  const input = testInfo.outputPath('input.json')
  await writeFile(input, files['input.json'] ?? new Uint8Array())

  const validated = await printedDocument('validate', input)
  const solved = await printedDocument('solve', input)

  expect(parsed(files, 'problem.json')).toEqual(withoutKeys(validated, 'input'))
  expect(withoutKeys(parsed(files, 'outcome.json'), 'environment')).toEqual(
    withoutKeys(solved, 'environment'),
  )
})
