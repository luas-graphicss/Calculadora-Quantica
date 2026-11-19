import type { Locator, Page } from '@playwright/test'

const FARTHEST_TAB_STOP = 120

async function isFocused(target: Locator): Promise<boolean> {
  return target.evaluate((element) => element === document.activeElement)
}

async function reach(page: Page, target: Locator, key: 'Tab' | 'Shift+Tab'): Promise<void> {
  for (let stop = 0; stop < FARTHEST_TAB_STOP; stop += 1) {
    await page.keyboard.press(key)
    if (await isFocused(target)) return
  }
  throw new Error(`The target was not reached with ${FARTHEST_TAB_STOP} presses of ${key}`)
}

export function tabTo(page: Page, target: Locator): Promise<void> {
  return reach(page, target, 'Tab')
}

export function tabBackTo(page: Page, target: Locator): Promise<void> {
  return reach(page, target, 'Shift+Tab')
}

export async function replaceWith(page: Page, text: string): Promise<void> {
  await page.keyboard.press('ControlOrMeta+a')
  await page.keyboard.type(text)
}

export async function typeInto(page: Page, field: Locator, text: string): Promise<void> {
  await tabTo(page, field)
  await page.keyboard.type(text)
}

export async function activate(page: Page, target: Locator): Promise<void> {
  await tabTo(page, target)
  await page.keyboard.press('Enter')
}

export async function chooseOption(page: Page, select: Locator, label: string): Promise<void> {
  await tabTo(page, select)
  const distance = await select.evaluate((element, wanted) => {
    if (!(element instanceof HTMLSelectElement)) throw new Error('The target is not a select')
    const position = [...element.options].findIndex((option) => option.label === wanted)
    if (position < 0) throw new Error(`The select has no option labelled ${wanted}`)
    return position - element.selectedIndex
  }, label)
  const key = distance > 0 ? 'ArrowDown' : 'ArrowUp'
  for (let press = 0; press < Math.abs(distance); press += 1) {
    await page.keyboard.press(key)
  }
}
