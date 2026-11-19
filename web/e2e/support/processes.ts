import { readdir, readFile } from 'node:fs/promises'

const PROCESS_DIRECTORY = /^\d+$/
const CALCULATION_MARKER = 'spawn_main'
const VANISHED = new Set(['ENOENT', 'ESRCH'])

function hasVanished(error: unknown): boolean {
  return error instanceof Error && 'code' in error && VANISHED.has(String(error.code))
}

async function readProcessFile(pid: number, name: string): Promise<string | null> {
  try {
    return await readFile(`/proc/${pid}/${name}`, 'utf8')
  } catch (error) {
    if (hasVanished(error)) return null
    throw error
  }
}

async function parentsByProcess(): Promise<Map<number, number>> {
  const parents = new Map<number, number>()
  for (const entry of await readdir('/proc')) {
    if (!PROCESS_DIRECTORY.test(entry)) continue
    const stat = await readProcessFile(Number(entry), 'stat')
    if (stat === null) continue
    const [, parent] = stat.slice(stat.lastIndexOf(')') + 2).split(' ')
    parents.set(Number(entry), Number(parent))
  }
  return parents
}

export async function descendantsOf(root: number): Promise<number[]> {
  const parents = await parentsByProcess()
  const found: number[] = []
  let generation = [root]
  while (generation.length > 0) {
    const children = [...parents]
      .filter(([, parent]) => generation.includes(parent))
      .map(([pid]) => pid)
    found.push(...children)
    generation = children
  }
  return found
}

export async function calculationProcessesOf(root: number): Promise<number[]> {
  const calculating: number[] = []
  for (const pid of await descendantsOf(root)) {
    const commandLine = await readProcessFile(pid, 'cmdline')
    if (commandLine?.includes(CALCULATION_MARKER)) calculating.push(pid)
  }
  return calculating
}

export function signalIfAlive(pid: number, signal: NodeJS.Signals): void {
  try {
    process.kill(pid, signal)
  } catch (error) {
    if (!hasVanished(error)) throw error
  }
}
