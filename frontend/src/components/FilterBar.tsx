import type { Filters, DateInterval } from "../hooks/useFilters"

interface Props {
  filters: Filters
  setFilter: <K extends keyof Filters>(key: K, value: Filters[K]) => void
  clearFilters: () => void
  services: string[]
}

const INTERVAL_OPTIONS: { value: DateInterval; label: string }[] = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "year", label: "Year" },
]

function ToggleButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`px-2 py-1 rounded text-xs border transition-colors ${
        active
          ? "bg-blue-600 text-white border-blue-600"
          : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
      }`}
    >
      {children}
    </button>
  )
}

export default function FilterBar({ filters, setFilter, clearFilters, services }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-2 px-4 py-2 bg-white border-b border-gray-200">
      {/* Donor input */}
      <input
        id="filter-text"
        type="search"
        placeholder="Donor name, ID…"
        value={filters.donor}
        onChange={(e) => setFilter("donor", e.target.value)}
        className="border border-gray-300 rounded px-2 py-1 text-sm w-44"
        aria-label="Donor search"
      />

      {/* Service dropdown */}
      <select
        value={filters.service}
        onChange={(e) => setFilter("service", e.target.value)}
        className="border border-gray-300 rounded px-2 py-1 text-sm"
        aria-label="Service filter"
      >
        <option value="">All Services</option>
        {services.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      {/* Toggle buttons */}
      <div className="flex items-center gap-1">
        <ToggleButton
          active={filters.missing}
          onClick={() => setFilter("missing", !filters.missing)}
        >
          Missing
        </ToggleButton>
        <ToggleButton
          active={filters.discrepancies}
          onClick={() => setFilter("discrepancies", !filters.discrepancies)}
        >
          Discrepancies
        </ToggleButton>
        <ToggleButton
          active={filters.duplicates}
          onClick={() => setFilter("duplicates", !filters.duplicates)}
        >
          Duplicates
        </ToggleButton>
      </div>

      {/* Date range UI (display only — logic in Phase 2) */}
      <div className="flex items-center gap-1">
        <input
          type="date"
          value={filters.dateStart}
          onChange={(e) => setFilter("dateStart", e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
          aria-label="Date start"
        />
        <select
          value={filters.dateInterval}
          onChange={(e) => setFilter("dateInterval", e.target.value as DateInterval)}
          className="border border-gray-300 rounded px-2 py-1 text-sm"
          aria-label="Date interval"
        >
          {INTERVAL_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {/* Amount range */}
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

      <button
        onClick={clearFilters}
        className="ml-auto text-xs text-gray-500 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-100"
      >
        Clear
      </button>
    </div>
  )
}
