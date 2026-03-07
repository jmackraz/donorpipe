import { useEffect, useCallback } from "react"
import type { Donation, Charge, Payout, Receipt } from "../lib/graph"
import type { EntityType } from "../hooks/useFilters"
import RelationshipGraph from "./RelationshipGraph"

type AnyEntity = Donation | Charge | Payout | Receipt

interface Props {
  type: EntityType
  entity: AnyEntity
  onClose: () => void
}

function fmtAmt(net: number, currency: string): string {
  return `${(net / 100).toFixed(2)} ${currency.toUpperCase()}`
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {})
}

function toFlatJson(type: EntityType, entity: AnyEntity): Record<string, unknown> {
  const base = {
    id: entity.id,
    service: entity.service,
    tx_id: entity.tx_id,
    date: entity.date,
    net: entity.net,
    currency: entity.currency,
  }
  if (type === "donations") {
    const d = entity as Donation
    return {
      ...base,
      name: d.name,
      email: d.email,
      designation: d.designation,
      comment: d.comment,
      payment_service: d.payment_service,
      charge_id: d.charge?.id ?? null,
      payout_id: d.payout?.id ?? null,
      receipt_ids: d.receipts.map((r) => r.id),
    }
  }
  if (type === "charges") {
    const c = entity as Charge
    return { ...base, name: c.name, description: c.description, payment_service: c.payment_service, payout_id: c.payout?.id ?? null }
  }
  if (type === "payouts") {
    const p = entity as Payout
    return { ...base, charge_ids: p.charges.map((c) => c.id) }
  }
  // receipts
  const r = entity as Receipt
  return {
    ...base,
    name: r.name,
    ref_id: r.ref_id,
    product: r.product,
    item_class: r.item_class,
    donation_id: r.donation?.id ?? null,
    discrepancies: r.discrepancies,
  }
}

function DonationDetail({ d }: { d: Donation }) {
  return (
    <>
      <section className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Provenance
        </h3>
        <dl className="text-sm space-y-0.5">
          <div className="flex gap-2">
            <dt className="text-gray-500 w-28 shrink-0">Service</dt>
            <dd className="font-mono">{d.service}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-gray-500 w-28 shrink-0">TX ID</dt>
            <dd className="font-mono">{d.tx_id}</dd>
          </div>
          {d.payment_service && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Payment</dt>
              <dd className="font-mono">{d.payment_service}</dd>
            </div>
          )}
          {d.email && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Email</dt>
              <dd>{d.email}</dd>
            </div>
          )}
          {d.designation && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Designation</dt>
              <dd>{d.designation}</dd>
            </div>
          )}
          {d.comment && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Comment</dt>
              <dd>{d.comment}</dd>
            </div>
          )}
        </dl>
      </section>

      <RelationshipGraph entity={d} />
    </>
  )
}

function ChargeDetail({ c }: { c: Charge }) {
  return (
    <>
      <section className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Provenance
        </h3>
        <dl className="text-sm space-y-0.5">
          <div className="flex gap-2">
            <dt className="text-gray-500 w-28 shrink-0">Service</dt>
            <dd className="font-mono">{c.service}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-gray-500 w-28 shrink-0">TX ID</dt>
            <dd className="font-mono">{c.tx_id}</dd>
          </div>
          {c.payment_service && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Payment</dt>
              <dd className="font-mono">{c.payment_service}</dd>
            </div>
          )}
          {c.description && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Description</dt>
              <dd>{c.description}</dd>
            </div>
          )}
        </dl>
      </section>

      <RelationshipGraph entity={c} />
    </>
  )
}

function PayoutDetail({ p }: { p: Payout }) {
  return <RelationshipGraph entity={p} />
}

function ReceiptDetail({ r }: { r: Receipt }) {
  return (
    <>
      <section className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Provenance
        </h3>
        <dl className="text-sm space-y-0.5">
          <div className="flex gap-2">
            <dt className="text-gray-500 w-28 shrink-0">Service</dt>
            <dd className="font-mono">{r.service}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-gray-500 w-28 shrink-0">TX ID</dt>
            <dd className="font-mono">{r.tx_id}</dd>
          </div>
          {r.ref_id && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Ref ID</dt>
              <dd className="font-mono">{r.ref_id}</dd>
            </div>
          )}
          {r.product && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Product</dt>
              <dd>{r.product}</dd>
            </div>
          )}
          {r.item_class && (
            <div className="flex gap-2">
              <dt className="text-gray-500 w-28 shrink-0">Class</dt>
              <dd>{r.item_class}</dd>
            </div>
          )}
        </dl>
      </section>

      {r.discrepancies.length > 0 && (
        <section className="mb-4">
          <h3 className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-1">
            ⚠ Discrepancies
          </h3>
          <ul className="text-sm text-amber-700 list-disc list-inside space-y-0.5">
            {r.discrepancies.map((d) => (
              <li key={d}>{d}</li>
            ))}
          </ul>
        </section>
      )}

      <RelationshipGraph entity={r} />
    </>
  )
}

const TYPE_LABELS: Record<EntityType, string> = {
  donations: "Donation",
  charges: "Charge",
  payouts: "Payout",
  receipts: "Receipt",
}

const TYPE_BADGE_COLORS: Record<EntityType, string> = {
  donations: "bg-blue-100 text-blue-700",
  charges: "bg-green-100 text-green-700",
  payouts: "bg-purple-100 text-purple-700",
  receipts: "bg-orange-100 text-orange-700",
}

export default function DetailPanel({ type, entity, onClose }: Props) {
  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    },
    [onClose],
  )

  useEffect(() => {
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [handleKey])

  return (
    <div
      className="w-full sm:w-96 border-l border-gray-200 bg-white overflow-y-auto flex-shrink-0"
      aria-label="Detail panel"
    >
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-xs font-medium rounded px-1.5 py-0.5 ${TYPE_BADGE_COLORS[type]}`}
            >
              {TYPE_LABELS[type]}
            </span>
            <span className="text-xs text-gray-500">{entity.date}</span>
          </div>
          {(type === "donations" || type === "receipts") &&
            (entity as Donation | Receipt).name && (
              <div className="text-base font-medium text-gray-800 truncate">
                {(entity as Donation | Receipt).name}
              </div>
            )}
          <div className="text-lg font-semibold text-gray-900">
            {fmtAmt(entity.net, entity.currency)}
          </div>
          <div className="font-mono text-xs text-gray-400 truncate mt-0.5">{entity.id}</div>
        </div>
        <div className="flex items-center gap-2 ml-2 shrink-0">
          <button
            onClick={() => copyToClipboard(entity.id)}
            className="text-xs text-gray-500 hover:text-gray-900 border border-gray-200 rounded px-2 py-1"
            title="Copy ID"
          >
            Copy ID
          </button>
          <button
            onClick={onClose}
            aria-label="Close detail panel"
            className="text-gray-400 hover:text-gray-700 text-lg leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="px-4 py-3">
        {type === "donations" && <DonationDetail d={entity as Donation} />}
        {type === "charges" && <ChargeDetail c={entity as Charge} />}
        {type === "payouts" && <PayoutDetail p={entity as Payout} />}
        {type === "receipts" && <ReceiptDetail r={entity as Receipt} />}

        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-gray-400 hover:text-gray-700 select-none">
            Raw JSON
          </summary>
          <pre className="mt-2 p-2 bg-gray-50 rounded overflow-auto text-xs text-gray-700 max-h-64">
            {JSON.stringify(toFlatJson(type, entity), null, 2)}
          </pre>
        </details>
      </div>
    </div>
  )
}
