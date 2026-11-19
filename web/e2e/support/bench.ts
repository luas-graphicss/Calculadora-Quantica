import { type ChildProcess, spawn } from 'node:child_process'
import { once } from 'node:events'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

import { COMMAND } from './command-line'
import { calculationProcessesOf, descendantsOf, signalIfAlive } from './processes'

const WEB_ROOT = process.env.QCALC_WEB_ROOT
const START_TIMEOUT_MS = 60_000
const STOP_TIMEOUT_MS = 20_000
const ORIGIN = /^Bancada em (http:\/\/127\.0\.0\.1:\d+)$/m
const LAUNCH_PAGE = /^Arquivo de acesso: (.+)$/m

type Address = {
  origin: string
  launchUrl: string
}

type Session = Address & {
  process: ChildProcess
}

function announcedAddress(child: ChildProcess): Promise<Address> {
  return new Promise((resolve, reject) => {
    let announced = ''
    let complaints = ''
    const fail = (reason: string) => {
      clearTimeout(deadline)
      reject(new Error(`${reason}\n${complaints}`))
    }
    const deadline = setTimeout(() => {
      fail(`qcalc serve did not announce its address within ${START_TIMEOUT_MS} ms`)
    }, START_TIMEOUT_MS)

    child.stderr?.on('data', (chunk: Buffer) => {
      complaints += chunk.toString()
    })
    child.stdout?.on('data', (chunk: Buffer) => {
      announced += chunk.toString()
      const origin = ORIGIN.exec(announced)?.[1]
      const launchPage = LAUNCH_PAGE.exec(announced)?.[1]
      if (origin === undefined || launchPage === undefined) return
      clearTimeout(deadline)
      resolve({ origin, launchUrl: pathToFileURL(launchPage).href })
    })
    child.once('error', (error) => {
      fail(`qcalc serve could not be started: ${error.message}`)
    })
    child.once('exit', (code) => {
      fail(`qcalc serve exited with code ${String(code)} before announcing its address`)
    })
  })
}

async function end(child: ChildProcess, signal: NodeJS.Signals): Promise<void> {
  if (child.exitCode !== null || child.signalCode !== null) return
  const exited = once(child, 'exit')
  const lastResort = setTimeout(() => child.kill('SIGKILL'), STOP_TIMEOUT_MS)
  child.kill(signal)
  await exited
  clearTimeout(lastResort)
}

export class Bench {
  private session: Session | null = null

  private constructor(readonly dataDirectory: string) {}

  static async onEmptyProfile(): Promise<Bench> {
    const bench = new Bench(await mkdtemp(path.join(tmpdir(), 'qcalc-bench-')))
    await bench.start()
    return bench
  }

  get origin(): string {
    return this.running().origin
  }

  get launchUrl(): string {
    return this.running().launchUrl
  }

  async start(): Promise<void> {
    if (this.session !== null) throw new Error('This bench is already running')
    const options = ['serve', '--data-dir', this.dataDirectory, '--port', '0', '--no-browser']
    if (WEB_ROOT !== undefined) options.push('--web-root', WEB_ROOT)
    const child = spawn(COMMAND, options, { detached: true, stdio: ['ignore', 'pipe', 'pipe'] })
    try {
      this.session = { process: child, ...(await announcedAddress(child)) }
    } catch (error) {
      await end(child, 'SIGKILL')
      throw error
    }
  }

  async stop(): Promise<void> {
    await this.endWith('SIGTERM')
  }

  async kill(): Promise<void> {
    await this.endWith('SIGKILL')
  }

  async calculationProcesses(): Promise<number[]> {
    const { pid } = this.running().process
    return pid === undefined ? [] : calculationProcessesOf(pid)
  }

  async remove(): Promise<void> {
    await this.stop()
    await rm(this.dataDirectory, { recursive: true, force: true })
  }

  private async endWith(signal: NodeJS.Signals): Promise<void> {
    const session = this.session
    if (session === null) return
    this.session = null
    const { pid } = session.process
    const descendants = pid === undefined ? [] : await descendantsOf(pid)
    await end(session.process, signal)
    for (const descendant of descendants) signalIfAlive(descendant, 'SIGKILL')
  }

  private running(): Session {
    if (this.session === null) throw new Error('This bench is not running')
    return this.session
  }
}
