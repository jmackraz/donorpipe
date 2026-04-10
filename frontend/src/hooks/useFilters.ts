import { useCallback, useMemo } from "react"
import { useSearchParams } from "react-router-dom"

export type EntityType = "donations" | "charges" | "payouts" | "receipts"
export type DateInterval = "day" | "week" | "month" | "year"

export interface Filters {
  type: EntityType
  donor: string
  missing: boolean
  discrepancies: boolean
  duplicates: boolean
  service: string
  dateStart: string
  dateInterval: DateInterval
  amountMin: number | null
  amountMax: number | null
  selected: string | null
  sortAsc: boolean
}

function isEntityType(v: string | null): v is EntityType {
  return v === "donations" || v === "charges" || v === "payouts" || v === "receipts"
}

function isDateInterval(v: string | null): v is DateInterval {
  return v === "day" || v === "week" || v === "month" || v === "year"
}

export function useFilters() {
  const [params, setParams] = useSearchParams()

  const filters: Filters = useMemo(() => {
    const rawType = params.get("type")
    const rawInterval = params.get("dateInterval")
    const type: EntityType = isEntityType(rawType) ? rawType : "donations"
    return {
      type,
      donor: params.get("donor") ?? "",
      missing: params.get("missing") === "1",
      discrepancies: params.get("discrepancies") === "1",
      duplicates: params.get("duplicates") === "1",
      service: params.get("service") ?? "",
      dateStart: params.get("dateStart") ?? "",
      dateInterval: isDateInterval(rawInterval) ? rawInterval : "month",
      amountMin: params.get("amountMin") ? Number(params.get("amountMin")) : null,
      amountMax: params.get("amountMax") ? Number(params.get("amountMax")) : null,
      selected: params.get(`sel_${type}`),
      sortAsc: params.get("sortAsc") === "1",
    }
  }, [params])

  const setFilter = useCallback(
    <K extends keyof Filters>(key: K, value: Filters[K]) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          if (value === null || value === "" || value === false) {
            next.delete(key)
          } else if (value === true) {
            next.set(key, "1")
          } else {
            next.set(key, String(value))
          }
          return next
        },
        { replace: true },
      )
    },
    [setParams],
  )

  const setSelected = useCallback(
    (id: string | null) => {
      const type = params.get("type") ?? "donations"
      const selKey = `sel_${type}`
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          if (id) next.set(selKey, id)
          else next.delete(selKey)
          return next
        },
        { replace: true },
      )
    },
    [params, setParams],
  )

  const clearFilters = useCallback(() => {
    setParams(
      (prev) => {
        const next = new URLSearchParams()
        for (const key of ["account", "type", "sel_donations", "sel_receipts", "sel_payouts"] as const) {
          const v = prev.get(key)
          if (v) next.set(key, v)
        }
        return next
      },
      { replace: true },
    )
  }, [setParams])

  return { filters, setFilter, setSelected, clearFilters }
}
