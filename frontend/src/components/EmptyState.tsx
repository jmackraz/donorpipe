interface Props {
  onClear: () => void
}

export default function EmptyState({ onClear }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3 p-8">
      <p className="text-sm">No results match these filters.</p>
      <button
        onClick={onClear}
        className="text-sm text-blue-600 hover:underline"
      >
        Clear filters
      </button>
    </div>
  )
}
