import { useRef, useEffect } from "react"
import { useVirtualizer } from "@tanstack/react-virtual"
import type { Donation, Charge, Payout, Receipt } from "../lib/graph"
import type { EntityType } from "../hooks/useFilters"

export type AnyEntity = Donation | Charge | Payout | Receipt

interface Props {
  type: EntityType
  entities: AnyEntity[]
  selectedId: string | null
  onSelect: (id: string) => void
}

function fmtAmt(net: number, currency: string): string {
  return `${(net / 100).toFixed(2)} ${currency.toUpperCase()}`
}

function DonationRow({ d }: { d: Donation }) {
  return (
    <>
      <span className="w-24 shrink-0 text-gray-500">{d.date}</span>
      <span className="flex-1 font-medium text-gray-900 truncate min-w-0">{d.name || "—"}</span>
      <span className="w-28 shrink-0 text-right tabular-nums">{fmtAmt(d.net, d.currency)}</span>
      <span className="w-28 shrink-0 text-gray-500 truncate hidden sm:block">
        {d.designation || "—"}
      </span>
      <span className="w-16 shrink-0 text-center">
        {d.charge ? (
          <span className="text-xs text-green-600 bg-green-50 rounded px-1">charge</span>
        ) : null}
      </span>
      <span className="w-16 shrink-0 text-center">
        {d.receipts.length > 0 ? (
          <span className="text-xs text-blue-600 bg-blue-50 rounded px-1">
            {d.receipts.length}r
          </span>
        ) : null}
      </span>
    </>
  )
}

function ChargeRow({ c }: { c: Charge }) {
  return (
    <>
      <span className="w-24 shrink-0 text-gray-500">{c.date}</span>
      <span className="flex-1 font-medium text-gray-900 truncate min-w-0">{c.name || "—"}</span>
      <span className="w-28 shrink-0 text-right tabular-nums">{fmtAmt(c.net, c.currency)}</span>
      <span className="w-36 shrink-0 text-gray-500 truncate hidden sm:block">
        {c.description || "—"}
      </span>
      <span className="w-24 shrink-0 text-center">
        {c.payout ? (
          <span className="text-xs text-purple-600 bg-purple-50 rounded px-1">paid out</span>
        ) : null}
      </span>
    </>
  )
}

function PayoutRow({ p }: { p: Payout }) {
  return (
    <>
      <span className="w-24 shrink-0 text-gray-500">{p.date}</span>
      <span className="flex-1 text-gray-900 truncate min-w-0 font-mono text-xs">{p.id}</span>
      <span className="w-28 shrink-0 text-right tabular-nums">{fmtAmt(p.net, p.currency)}</span>
      <span className="w-24 shrink-0 text-gray-500 text-center">{p.charges.length} charges</span>
    </>
  )
}

function ReceiptRow({ r }: { r: Receipt }) {
  return (
    <>
      <span className="w-24 shrink-0 text-gray-500">{r.date}</span>
      <span className="flex-1 font-medium text-gray-900 truncate min-w-0">{r.name || "—"}</span>
      <span className="w-28 shrink-0 text-right tabular-nums">{fmtAmt(r.net, r.currency)}</span>
      <span className="w-28 shrink-0 text-gray-500 truncate hidden sm:block">
        {r.product || "—"}
      </span>
      <span className="w-16 shrink-0 text-center">
        {r.donation ? (
          <span className="text-xs text-green-600 bg-green-50 rounded px-1">matched</span>
        ) : null}
      </span>
      <span className="w-20 shrink-0">
        {r.discrepancies.length > 0 ? (
          <span className="text-xs text-amber-600 bg-amber-50 rounded px-1">
            ⚠ {r.discrepancies.length}
          </span>
        ) : null}
      </span>
    </>
  )
}

function EntityRow({ type, entity }: { type: EntityType; entity: AnyEntity }) {
  if (type === "donations") return <DonationRow d={entity as Donation} />
  if (type === "charges") return <ChargeRow c={entity as Charge} />
  if (type === "payouts") return <PayoutRow p={entity as Payout} />
  return <ReceiptRow r={entity as Receipt} />
}

const ROW_HEIGHT = 48

export default function EntityTable({ type, entities, selectedId, onSelect }: Props) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: entities.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 8,
  })

  const selectedIndex = selectedId ? entities.findIndex((e) => e.id === selectedId) : -1

  // Keyboard navigation
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      const target = e.target as Element
      if (target.tagName === "INPUT" || target.tagName === "SELECT") return

      if (e.key === "ArrowDown") {
        e.preventDefault()
        const next = selectedIndex < entities.length - 1 ? selectedIndex + 1 : 0
        const entity = entities[next]
        if (entity) {
          onSelect(entity.id)
          virtualizer.scrollToIndex(next, { align: "auto" })
        }
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        const prev = selectedIndex > 0 ? selectedIndex - 1 : entities.length - 1
        const entity = entities[prev]
        if (entity) {
          onSelect(entity.id)
          virtualizer.scrollToIndex(prev, { align: "auto" })
        }
      } else if (e.key === "c" && selectedId) {
        navigator.clipboard.writeText(selectedId).catch(() => {})
      }
    }

    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [selectedIndex, entities, onSelect, virtualizer, selectedId])

  return (
    <div ref={parentRef} className="flex-1 overflow-auto" tabIndex={-1}>
      <div
        style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}
      >
        {virtualizer.getVirtualItems().map((vItem) => {
          const entity = entities[vItem.index]
          if (!entity) return null
          const isSelected = entity.id === selectedId
          return (
            <div
              key={entity.id}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: `${vItem.size}px`,
                transform: `translateY(${vItem.start}px)`,
              }}
              role="row"
              aria-selected={isSelected}
              className={`flex items-center gap-2 px-4 text-sm cursor-pointer border-b border-gray-100 transition-colors ${
                isSelected ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
              onClick={() => onSelect(entity.id)}
            >
              <EntityRow type={type} entity={entity} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
