import { createHash } from 'node:crypto'
import { readFile, writeFile } from 'node:fs/promises'

import type { Download, Page } from '@playwright/test'
import { strFromU8, strToU8, unzipSync, zipSync } from 'fflate'

export type PackageFiles = Record<string, Uint8Array>

type ListedFile = {
  path: string
  sha256: string
  size: number
}

export type Manifest = {
  files: ListedFile[]
  generator: { name: string; version: string }
  run: { package_version: string }
}

const MANIFEST = 'manifest.json'

export async function savedPackage(download: Download, destination: string): Promise<PackageFiles> {
  await download.saveAs(destination)
  return unzipSync(new Uint8Array(await readFile(destination)))
}

export async function exportPackage(page: Page, destination: string): Promise<PackageFiles> {
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('link', { name: 'Exportar pacote' }).click(),
  ])
  return savedPackage(download, destination)
}

export async function writePackage(destination: string, files: PackageFiles): Promise<void> {
  await writeFile(destination, zipSync(files))
}

export function textOf(files: PackageFiles, name: string): string {
  const content = files[name]
  if (content === undefined) throw new Error(`The package has no file ${name}`)
  return strFromU8(content)
}

export function manifestOf(files: PackageFiles): Manifest {
  return JSON.parse(textOf(files, MANIFEST)) as Manifest
}

export function withText(files: PackageFiles, name: string, text: string): PackageFiles {
  return { ...files, [name]: strToU8(text) }
}

export function withManifest(files: PackageFiles, manifest: Manifest): PackageFiles {
  return withText(files, MANIFEST, JSON.stringify(manifest))
}

export function sha256(content: Uint8Array): string {
  return createHash('sha256').update(content).digest('hex')
}

export async function importPackage(page: Page, file: string): Promise<void> {
  await page.getByLabel('Importar pacote').setInputFiles(file)
}
