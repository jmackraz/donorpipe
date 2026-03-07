import { useState, useMemo } from "react"
import type { TransactionStore } from "../lib/graph"

interface Props {
  store: TransactionStore
}

interface ServiceStats {
  count: number
  oldest: string
  newest: string
}

export default function StatsBar({ store }: Props) {
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
