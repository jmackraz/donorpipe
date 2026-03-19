import { useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

async function fetchHelp(): Promise<string> {
  const res = await fetch("/help")
  if (!res.ok) throw new Error(`Failed to load help (${res.status})`)
  return res.text()
}

interface HelpModalProps {
  onClose: () => void
}

export default function HelpModal({ onClose }: HelpModalProps) {
  const { data, isLoading, error } = useQuery({ queryKey: ["help"], queryFn: fetchHelp })

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.metaKey || e.ctrlKey) return
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 overflow-y-auto"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-white w-full max-w-3xl mx-auto my-8 rounded-lg shadow-xl flex flex-col">
        {/* Sticky header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 sticky top-8 bg-white rounded-t-lg">
          <h2 className="text-lg font-semibold text-gray-900">Help</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Close help"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          {isLoading && (
            <p className="text-sm text-gray-400">Loading…</p>
          )}
          {error && (
            <p className="text-sm text-red-500">Could not load help content.</p>
          )}
          {data && (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{data}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
