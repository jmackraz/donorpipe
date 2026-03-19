import { useState, useMemo } from "react"
import type { TransactionStore } from "../lib/graph"

const STALE_HOURS = 48

function formatUpdated(isoString: string): { label: string; stale: boolean } {
  const dt = new Date(isoString)
  const now = new Date()
  const ageMs = now.getTime() - dt.getTime()
  const stale = ageMs > STALE_HOURS * 60 * 60 * 1000
  const label = dt.toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  })
  return { label, stale }
}

interface Props {
  store: TransactionStore
  newDataAvailable?: boolean
  onReload?: () => void
  refreshPending?: boolean
  onRequestRefresh?: () => void
}

interface ServiceStats {
  count: number
  oldest: string
  newest: string
}

export default function StatsBar({ store, newDataAvailable, onReload, refreshPending, onRequestRefresh }: Props) {
  const [open, setOpen] = useState(false)

  const stats = useMemo(() => {
    const services = new Map<string, ServiceStats>()

    for (const map of [store.donations, store.charges, store.payouts, store.receipts]) {
      for (const e of map.values()) {
        const s = services.get(e.service) ?? { count: 0, oldest: e.date, newest: e.date }
        s.count++
        if (e.date < s.oldest) s.oldest = e.date
        if (e.date > s.newest) s.newest = e.date
        services.set(e.service, s)
      }
    }

    return {
      totals: {
        donations: store.donations.size,
        charges: store.charges.size,
        payouts: store.payouts.size,
        receipts: store.receipts.size,
      },
      services,
    }
  }, [store])

  const { totals } = stats
  const updated = store.meta ? formatUpdated(store.meta.generated_at) : null

  return (
    <div className="bg-gray-50 border-b border-gray-200">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="w-full px-4 py-1.5 text-xs text-left text-gray-500 flex items-center gap-2 hover:text-gray-700"
      >
        <span>{open ? "▲" : "▼"}</span>
        <span>
          {totals.donations} donations · {totals.payouts} payouts ·{" "}
          {totals.receipts} receipts
        </span>
        {newDataAvailable ? (
          <span
            className="ml-auto text-amber-600 hover:text-amber-800 cursor-pointer underline"
            onClick={(e) => { e.stopPropagation(); onReload?.() }}
            role="button"
            tabIndex={0}
          >
            New data — Reload ↺
          </span>
        ) : refreshPending ? (
          <span className="ml-auto text-amber-600">
            Refreshing…
          </span>
        ) : updated ? (
          <span className={`ml-auto flex items-center gap-2 ${updated.stale ? "text-amber-600" : "text-gray-400"}`}>
            <span>Updated {updated.label}</span>
            <span
              className="cursor-pointer hover:text-gray-600"
              onClick={(e) => { e.stopPropagation(); onRequestRefresh?.() }}
              role="button"
              tabIndex={0}
              title="Request data refresh"
              aria-label="Request data refresh"
            >
              ↻
            </span>
          </span>
        ) : null}
      </button>

      {open && (
        <div className="px-4 pb-3 text-xs text-gray-600 space-y-1">
          {[...stats.services.entries()].map(([service, s]) => (
            <div key={service} className="flex gap-3">
              <span className="font-medium w-28 truncate">{service}</span>
              <span>{s.count} entities</span>
              <span className="text-gray-400">
                {s.oldest} – {s.newest}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
