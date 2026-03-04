import type { EntityType } from "../hooks/useFilters"
import type { TransactionStore } from "../lib/graph"

interface Props {
  activeType: EntityType
  store: TransactionStore
  onSelect: (type: EntityType) => void
}

const TABS: { type: EntityType; label: string }[] = [
  { type: "donations", label: "Donations" },
  { type: "charges", label: "Charges" },
  { type: "payouts", label: "Payouts" },
  { type: "receipts", label: "Receipts" },
]

export default function TypeTabs({ activeType, store, onSelect }: Props) {
  return (
    <div role="tablist" className="flex border-b border-gray-200 bg-white px-4">
      {TABS.map(({ type, label }, i) => {
        const count = store[type].size
        const active = type === activeType
        return (
          <button
            key={type}
            role="tab"
            aria-selected={active}
            onClick={() => onSelect(type)}
            title={`${label} (${i + 1})`}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              active
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            {label}{" "}
            <span className="text-xs opacity-70">({count})</span>
          </button>
        )
      })}
    </div>
  )
}
