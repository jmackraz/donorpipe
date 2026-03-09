import { useMemo, useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { useAuth } from "../contexts/AuthContext"
import { useGraph } from "../hooks/useGraph"
import { useFilters } from "../hooks/useFilters"
import type { EntityType } from "../hooks/useFilters"
import { filterDonations, filterPayouts, filterReceipts } from "../lib/filters"
import type { AnyEntity } from "./EntityTable"
import TypeTabs from "./TypeTabs"
import FilterBar from "./FilterBar"
import EntityTable from "./EntityTable"
import DetailPanel from "./DetailPanel"
import StatsBar from "./StatsBar"
import EmptyState from "./EmptyState"
import ErrorBanner from "./ErrorBanner"

export default function AppLayout() {
  const [searchParams, setSearchParams] = useSearchParams()
  const account = searchParams.get("account") ?? ""
  const { accounts } = useAuth()

  // Local input state — only pushed to URL on form submit
  const [accountInput, setAccountInput] = useState(account)

  // Auto-select first account when accounts load and no account is in URL
  useEffect(() => {
    if (accounts.length > 0 && !account) {
      const first = accounts[0]
      setAccountInput(first)
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          next.set("account", first)
          next.delete("selected")
          return next
        },
        { replace: true },
      )
    }
  }, [accounts]) // eslint-disable-line react-hooks/exhaustive-deps

  const { data: store, isLoading, error, refetch } = useGraph(account)
  const { filters, setFilter, clearFilters } = useFilters()

  // Tab keyboard shortcuts 1–4 and "/" to focus filter text
  useEffect(() => {
    const types: EntityType[] = ["donations", "payouts", "receipts"]
    function handleKey(e: KeyboardEvent) {
      const target = e.target as Element
      if (target.tagName === "INPUT" || target.tagName === "SELECT") return
      if (/^[1-3]$/.test(e.key)) {
        const t = types[parseInt(e.key) - 1]
        if (t) setFilter("type", t)
      } else if (e.key === "/") {
        e.preventDefault()
        document.getElementById("filter-text")?.focus()
      }
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [setFilter])

  const receiptServices = useMemo(
    () =>
      store
        ? [...new Set([...store.receipts.values()].map((r) => r.service))].sort()
        : [],
    [store],
  )

  const filteredEntities = useMemo((): AnyEntity[] => {
    if (!store) return []
    switch (filters.type) {
      case "donations":
        return filterDonations(store.donations, filters)
      case "payouts":
        return filterPayouts(store.payouts, filters)
      case "receipts":
        return filterReceipts(store.receipts, filters)
    }
  }, [store, filters])

  const selectedEntity = useMemo((): AnyEntity | null => {
    if (!store || !filters.selected) return null
    return (
      store.donations.get(filters.selected) ??
      store.payouts.get(filters.selected) ??
      store.receipts.get(filters.selected) ??
      null
    )
  }, [store, filters.selected])

  function handleAccountSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (accountInput) next.set("account", accountInput)
        else next.delete("account")
        next.delete("selected")
        return next
      },
      { replace: true },
    )
  }

  function handleAccountChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const val = e.target.value
    setAccountInput(val)
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (val) next.set("account", val)
        else next.delete("account")
        next.delete("selected")
        return next
      },
      { replace: true },
    )
  }

  const hasData = !!store

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-4 shrink-0">
        <h1 className="text-lg font-bold text-gray-900 shrink-0">DonorPipe</h1>
        {accounts.length === 1 ? (
          <span className="text-sm text-gray-600">{account}</span>
        ) : accounts.length > 1 ? (
          <select
            className="border border-gray-300 rounded px-3 py-1.5 text-sm"
            value={account}
            onChange={handleAccountChange}
            aria-label="Account"
          >
            {accounts.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        ) : (
          <form onSubmit={handleAccountSubmit} className="flex gap-2">
            <input
              className="border border-gray-300 rounded px-3 py-1.5 text-sm w-44"
              placeholder="Account ID"
              value={accountInput}
              onChange={(e) => setAccountInput(e.target.value)}
              aria-label="Account ID"
            />
            <button
              type="submit"
              disabled={isLoading || !accountInput}
              className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? "Loading…" : "Fetch"}
            </button>
          </form>
        )}
      </header>

      {/* Stats bar */}
      {store && <StatsBar store={store} />}

      {/* Error */}
      {error && <ErrorBanner error={error as Error} onRetry={() => refetch()} />}

      {/* Loading */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
          Loading…
        </div>
      )}

      {/* Main content */}
      {hasData && !isLoading && (
        <>
          <TypeTabs
            activeType={filters.type}
            store={store}
            onSelect={(t) => {
              setSearchParams(
                (prev) => {
                  const next = new URLSearchParams(prev)
                  next.set("type", t)
                  next.delete("selected")
                  return next
                },
                { replace: true },
              )
            }}
          />

          <FilterBar filters={filters} setFilter={setFilter} clearFilters={clearFilters} services={receiptServices} />

          <div className="flex flex-1 overflow-hidden">
            {/* List pane — hidden on mobile when detail panel is open */}
            <div
              className={`flex flex-col flex-1 overflow-hidden ${
                selectedEntity ? "hidden sm:flex" : "flex"
              }`}
            >
              {filteredEntities.length === 0 ? (
                <EmptyState onClear={clearFilters} />
              ) : (
                <EntityTable
                  type={filters.type}
                  entities={filteredEntities}
                  selectedId={filters.selected}
                  onSelect={(id) => setFilter("selected", id)}
                />
              )}
            </div>

            {/* Detail panel */}
            {selectedEntity && (
              <DetailPanel
                type={filters.type}
                entity={selectedEntity}
                onClose={() => setFilter("selected", null)}
              />
            )}
          </div>
        </>
      )}

      {/* Empty start state */}
      {!hasData && !isLoading && !error && (
        <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
          {accounts.length === 0 ? "Enter an account ID and click Fetch." : "Loading…"}
        </div>
      )}
    </div>
  )
}
