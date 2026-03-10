import { useRef, useEffect } from "react"
import type { Filters, DateInterval } from "../hooks/useFilters"

interface Props {
  filters: Filters
  setFilter: <K extends keyof Filters>(key: K, value: Filters[K]) => void
  clearFilters: () => void
  services: string[]
  isOpen: boolean
  onToggle: () => void
  onClose: () => void
}

function DateInput({
  value,
  onChange,
  label,
}: {
  value: string
  onChange: (v: string) => void
  label: string
}) {
  const ref = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (ref.current && ref.current.value !== value) {
      ref.current.value = value
    }
  }, [value])

  return (
    <input
      ref={ref}
      type="date"
      defaultValue={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-gray-300 rounded px-2 py-1 text-sm"
      aria-label={label}
    />
  )
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

export default function FilterBar({ filters, setFilter, clearFilters, services, isOpen, onToggle, onClose }: Props) {
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handlePointerDown(e: PointerEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    if (isOpen) {
      document.addEventListener("pointerdown", handlePointerDown)
    }
    return () => document.removeEventListener("pointerdown", handlePointerDown)
  }, [isOpen, onClose])

  const hasActiveFilters = !!(
    filters.donor ||
    filters.service ||
    filters.amountMin !== null ||
    filters.amountMax !== null ||
    filters.missing ||
    filters.discrepancies ||
    filters.duplicates
  )

  return (
    <div ref={panelRef} className="bg-white border-b border-gray-200 shrink-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-4 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 select-none"
        aria-expanded={isOpen}
        aria-controls="filter-panel-body"
      >
        <span className="font-medium text-gray-700">Filters</span>
        {hasActiveFilters && (
          <span className="text-xs bg-blue-100 text-blue-700 rounded-full px-1.5 py-0.5">active</span>
        )}
        <span className={`ml-auto text-gray-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}>
          ▾
        </span>
      </button>

      <div
        id="filter-panel-body"
        className={`grid transition-[grid-template-rows] duration-200 ${isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}
      >
        <div className="overflow-hidden">
          <div className="flex flex-wrap items-center gap-2 px-4 py-2">
            <div className="flex items-center gap-1">
              <DateInput
                value={filters.dateStart}
                onChange={(v) => setFilter("dateStart", v)}
                label="Date start"
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

            <button
              onClick={clearFilters}
              className="ml-auto text-xs text-gray-500 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-100"
            >
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
