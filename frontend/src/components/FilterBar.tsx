import type { Filters, DonationMatch } from "../hooks/useFilters"

interface Props {
  filters: Filters
  setFilter: <K extends keyof Filters>(key: K, value: Filters[K]) => void
  clearFilters: () => void
}

const MATCH_OPTIONS: { value: DonationMatch; label: string }[] = [
  { value: "all", label: "All" },
  { value: "has_charge", label: "Has charge" },
  { value: "has_receipt", label: "Has receipt" },
  { value: "unmatched", label: "Unmatched" },
]

export default function FilterBar({ filters, setFilter, clearFilters }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2 px-4 py-2 bg-white border-b border-gray-200">
      <input
        id="filter-text"
        type="search"
        placeholder="Search name, ID…"
        value={filters.text}
        onChange={(e) => setFilter("text", e.target.value)}
        className="border border-gray-300 rounded px-2 py-1 text-sm w-44"
        aria-label="Text search"
      />

      <div className="flex items-center gap-1">
        <input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => setFilter("dateFrom", e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
          aria-label="Date from"
        />
        <span className="text-gray-400 text-xs">–</span>
        <input
          type="date"
          value={filters.dateTo}
          onChange={(e) => setFilter("dateTo", e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
          aria-label="Date to"
        />
      </div>

      <div className="flex items-center gap-1">
        <input
          type="number"
          placeholder="Min $"
          min={0}
          value={filters.amountMin ?? ""}
          onChange={(e) =>
            setFilter("amountMin", e.target.value ? Number(e.target.value) : null)
          }
          className="border border-gray-300 rounded px-2 py-1 text-sm w-20"
          aria-label="Minimum amount"
        />
        <input
          type="number"
          placeholder="Max $"
          min={0}
          value={filters.amountMax ?? ""}
          onChange={(e) =>
            setFilter("amountMax", e.target.value ? Number(e.target.value) : null)
          }
          className="border border-gray-300 rounded px-2 py-1 text-sm w-20"
          aria-label="Maximum amount"
        />
      </div>

      {filters.type === "donations" && (
        <select
          value={filters.donationMatch}
          onChange={(e) => setFilter("donationMatch", e.target.value as DonationMatch)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
          aria-label="Relationship filter"
        >
          {MATCH_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      )}

      <button
        onClick={clearFilters}
        className="ml-auto text-xs text-gray-500 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-100"
      >
        Clear
      </button>
    </div>
  )
}
