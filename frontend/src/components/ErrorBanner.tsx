interface Props {
  error: Error
  onRetry: () => void
}

export default function ErrorBanner({ error, onRetry }: Props) {
  return (
    <div
      role="alert"
      className="bg-red-50 border border-red-200 rounded m-4 p-4 text-sm text-red-700 flex items-center justify-between"
    >
      <span>{error.message}</span>
      <button
        onClick={onRetry}
        className="ml-4 text-red-700 underline hover:no-underline"
      >
        Retry
      </button>
    </div>
  )
}
