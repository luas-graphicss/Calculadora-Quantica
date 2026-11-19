import { Upload } from 'lucide-react'
import { useState } from 'react'
import { useSWRConfig } from 'swr'

import { importPackage } from '@/shared/api/client'
import { describeError } from '@/shared/api/http'
import { RUNS_KEY } from '@/shared/api/queries'
import { secondaryButton } from '@/shared/components/button-styles'
import { Notice } from '@/shared/components/notice'
import { navigate } from '@/shared/routing/use-route'

export function ImportPackageButton() {
  const [isImporting, setIsImporting] = useState(false)
  const [problem, setProblem] = useState<string>()
  const { mutate } = useSWRConfig()

  async function importFrom(file: File) {
    setIsImporting(true)
    setProblem(undefined)
    try {
      const run = await importPackage(file)
      await mutate(RUNS_KEY)
      navigate({ name: 'run', identifier: run.identifier })
    } catch (error) {
      setProblem(describeError(error))
    } finally {
      setIsImporting(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <label
          className={`${secondaryButton} cursor-pointer focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-primary`}
        >
          <Upload className="size-4" aria-hidden="true" />
          {isImporting ? 'Importando…' : 'Importar pacote'}
          <input
            type="file"
            accept=".zip,application/zip"
            disabled={isImporting}
            className="sr-only"
            onChange={(event) => {
              const file = event.target.files?.[0]
              event.target.value = ''
              if (file !== undefined) void importFrom(file)
            }}
          />
        </label>
      </div>
      {problem === undefined ? null : (
        <Notice tone="problem" title="O pacote não foi importado">
          {problem}
        </Notice>
      )}
    </div>
  )
}
