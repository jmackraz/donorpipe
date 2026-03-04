import { useEffect, useState } from "react"
import { fromGraph } from "./lib/graph"
import type { TransactionStore } from "./lib/graph"
import type { EntityGraph } from "./lib/types"
import DonationList from "./components/DonationList"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

interface Timing {
  fetchMs: number
  decodeMs: number
}

function getAccount(): string {
  const params = new URLSearchParams(window.location.search)
  return params.get("account") ?? ""
}

export default function App() {
  const [account, setAccount] = useState(getAccount)
  const [store, setStore] = useState<TransactionStore | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [timing, setTiming] = useState<Timing | null>(null)

  async function fetchGraph(acct: string) {
    if (!acct) return
    setLoading(true)
    setError(null)
    try {
      const url = `${API_BASE}/accounts/${acct}/graph`
      const t0 = performance.now()
      const res = await fetch(url)
      const t1 = performance.now()
      if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}`)
      }
      const data = (await res.json()) as EntityGraph
      const t2 = performance.now()
      const decoded = fromGraph(data)
      const t3 = performance.now()
      setStore(decoded)
      setTiming({ fetchMs: t1 - t0, decodeMs: t3 - t2 })
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setStore(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (account) fetchGraph(account)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    fetchGraph(account)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">DonorPipe</h1>
      </header>

      <form onSubmit={handleSubmit} className="mb-4 flex gap-2">
        <input
          className="border border-gray-300 rounded px-3 py-1.5 text-sm flex-1 max-w-xs"
          placeholder="Account ID"
          value={account}
          onChange={(e) => setAccount(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading || !account}
          className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Loading…" : "Fetch"}
        </button>
      </form>

      {timing && (
        <p className="text-xs text-gray-500 mb-4">
          fetch {timing.fetchMs.toFixed(0)} ms · decode {timing.decodeMs.toFixed(0)} ms
        </p>
      )}

      {error && (
        <p className="text-red-600 text-sm mb-4">Error: {error}</p>
      )}

      {store && (
        <DonationList donations={store.donations} />
      )}
    </div>
  )
}
