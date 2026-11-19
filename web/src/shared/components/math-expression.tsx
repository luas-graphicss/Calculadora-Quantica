import katex from 'katex'
import { useEffect, useRef } from 'react'

type Props = {
  latex: string
  block?: boolean
}

const ERROR_COLOR = '#9a3412'

export function MathExpression({ latex, block = false }: Props) {
  const container = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const element = container.current
    if (element === null) return undefined
    katex.render(latex, element, {
      displayMode: block,
      errorColor: ERROR_COLOR,
      output: 'htmlAndMathml',
      throwOnError: false,
    })
    return () => {
      element.replaceChildren()
    }
  }, [latex, block])

  return <span ref={container} className={block ? 'block overflow-x-auto py-1' : undefined} />
}
