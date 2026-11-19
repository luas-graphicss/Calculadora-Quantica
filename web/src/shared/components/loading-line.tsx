type Props = {
  label: string
}

export function LoadingLine({ label }: Props) {
  return (
    <p role="status" className="text-sm text-muted">
      {`${label}…`}
    </p>
  )
}
