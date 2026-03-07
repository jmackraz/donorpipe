import { useCallback, useMemo } from "react"
import { useSearchParams } from "react-router-dom"

export type EntityType = "donations" | "payouts" | "receipts"
export type DonationMatch = "all" | "has_charge" | "has_receipt" | "unmatched"

export interface Filters {
  type: EntityType
  dateFrom: string
  dateTo: string
  text: string
  amountMin: number | null
  amountMax: number | null
  donationMatch: DonationMatch
  selected: string | null
}

function isEntityType(v: string | null): v is EntityType {
  return v === "donations" || v === "payouts" || v === "receipts"
}

function isDonationMatch(v: string | null): v is DonationMatch {
  return v === "all" || v === "has_charge" || v === "has_receipt" || v === "unmatched"
}

export function useFilters() {
  const [params, setParams] = useSearchParams()

  const filters: Filters = useMemo(() => {
    const rawType = params.get("type")
    const rawMatch = params.get("donationMatch")
    return {
      type: isEntityType(rawType) ? rawType : "donations",
      dateFrom: params.get("dateFrom") ?? "",
      dateTo: params.get("dateTo") ?? "",
      text: params.get("text") ?? "",
      amountMin: params.get("amountMin") ? Number(params.get("amountMin")) : null,
      amountMax: params.get("amountMax") ? Number(params.get("amountMax")) : null,
      donationMatch: isDonationMatch(rawMatch) ? rawMatch : "all",
      selected: params.get("selected"),
    }
  }, [params])

  const setFilter = useCallback(
    <K extends keyof Filters>(key: K, value: Filters[K]) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          if (value === null || value === "") {
            next.delete(key)
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

  const clearFilters = useCallback(() => {
    setParams(
      (prev) => {
        const next = new URLSearchParams()
        for (const key of ["account", "type"] as const) {
          const v = prev.get(key)
          if (v) next.set(key, v)
        }
        // Dates reset to defaults (omit from URL → defaults applied on next read)
        return next
      },
      { replace: true },
    )
  }, [setParams])

  return { filters, setFilter, clearFilters }
}
