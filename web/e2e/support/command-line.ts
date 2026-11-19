import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

export const COMMAND = process.env.QCALC_COMMAND ?? 'qcalc'

const run = promisify(execFile)
const OUTPUT_LIMIT_BYTES = 16 * 1024 * 1024

export async function printedDocument(...options: string[]): Promise<Record<string, unknown>> {
  const { stdout } = await run(COMMAND, [...options, '--format', 'json'], {
    maxBuffer: OUTPUT_LIMIT_BYTES,
  })
  return JSON.parse(stdout) as Record<string, unknown>
}
