import { useEffect, useCallback, useState } from "react"
import type { Donation, Charge, Payout, Receipt } from "../lib/graph"
import type { EntityType } from "../hooks/useFilters"
import { findBestDonation } from "../lib/matching"
import RelationshipGraph from "./RelationshipGraph"

type AnyEntity = Donation | Charge | Payout | Receipt

interface Props {
  type: EntityType
  entity: AnyEntity
  onClose: () => void
  donations: Map<string, Donation>
}

function fmtAmt(net: number, currency: string): string {
  return `${net.toFixed(2)} ${currency.toUpperCase()}`
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {})
}

function CopyButton({ text }: { text: string }) {
  return (
    <button
      onClick={() => copyToClipboard(text)}
      className="ml-1 text-gray-300 hover:text-gray-600 flex-shrink-0"
      title={`Copy`}
    >
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    </button>
  )
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

type OnSelectGraphEntity = (entity: Payout | Donation | Receipt) => void

function DonationDetail({ d, onSelectEntity }: { d: Donation; onSelectEntity?: OnSelectGraphEntity }) {
  return (
    <>
      <section className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Provenance
        </h3>
        <dl className="text-sm space-y-0.5">
          <div className="flex gap-2 items-center">
            <dt className="text-gray-500 w-28 shrink-0">Service</dt>
            <dd className="font-mono">{d.service}</dd>
            <CopyButton text={d.service} />
          </div>
          <div className="flex gap-2 items-center">
            <dt className="text-gray-500 w-28 shrink-0">TX ID</dt>
            <dd className="font-mono">{d.tx_id}</dd>
            <CopyButton text={d.tx_id} />
          </div>
          {d.payment_service && (
            <div className="flex gap-2 items-center">
              <dt className="text-gray-500 w-28 shrink-0">Payment</dt>
              <dd className="font-mono">{d.payment_service}</dd>
              <CopyButton text={d.payment_service} />
            </div>
          )}
          {d.email && (
            <div className="flex gap-2 items-center">
              <dt className="text-gray-500 w-28 shrink-0">Email</dt>
              <dd>{d.email}</dd>
              <CopyButton text={d.email} />
            </div>
          )}
          {d.designation && (
            <div className="flex gap-2 items-center">
              <dt className="text-gray-500 w-28 shrink-0">Designation</dt>
              <dd>{d.designation}</dd>
              <CopyButton text={d.designation} />
            </div>
          )}
          {d.comment && (
            <div className="flex gap-2 items-center">
              <dt className="text-gray-500 w-28 shrink-0">Comment</dt>
              <dd>{d.comment}</dd>
              <CopyButton text={d.comment} />
            </div>
          )}
        </dl>
      </section>

      <RelationshipGraph entity={d} onSelectEntity={onSelectEntity} />
    </>
  )
}

function ChargeDetail({ c, onSelectEntity }: { c: Charge; onSelectEntity?: OnSelectGraphEntity }) {
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

      <RelationshipGraph entity={c} onSelectEntity={onSelectEntity} />
    </>
  )
}

function PayoutDetail({ p, onSelectEntity }: { p: Payout; onSelectEntity?: OnSelectGraphEntity }) {
  return <RelationshipGraph entity={p} onSelectEntity={onSelectEntity} />
}

function ReceiptDetail({ r, onFindDonation, onSelectEntity }: { r: Receipt; onFindDonation?: () => void; onSelectEntity?: OnSelectGraphEntity }) {
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

      <RelationshipGraph entity={r} onSelectEntity={onSelectEntity} />

      {!r.donation && r.product !== "Direct Cash Donation" && onFindDonation && (
        <section className="mt-4">
          <button
            onClick={onFindDonation}
            className="text-sm text-blue-600 hover:text-blue-800 border border-blue-200 hover:border-blue-400 rounded px-3 py-1.5"
          >
            Find Donation
          </button>
        </section>
      )}
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

export default function DetailPanel({ type, entity, onClose, donations }: Props) {
  const [guessedDonation, setGuessedDonation] = useState<Donation | null | "none">(null)
  const [poppedEntity, setPoppedEntity] = useState<{ type: EntityType; entity: AnyEntity } | null>(null)

  useEffect(() => {
    setGuessedDonation(null)
    setPoppedEntity(null)
  }, [entity.id])

  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) return
      if (e.key === "Escape") {
        if (poppedEntity !== null) setPoppedEntity(null)
        else if (guessedDonation !== null) setGuessedDonation(null)
        else onClose()
      }
    },
    [onClose, guessedDonation, poppedEntity],
  )

  useEffect(() => {
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [handleKey])

  function handleFindDonation() {
    const result = findBestDonation(entity as Receipt, donations)
    setGuessedDonation(result ?? "none")
  }

  function handleSelectGraphEntity(graphEntity: Payout | Donation | Receipt) {
    let t: EntityType
    if ("charges" in graphEntity) t = "payouts"
    else if ("receipts" in graphEntity) t = "donations"
    else t = "receipts"
    setPoppedEntity({ type: t, entity: graphEntity })
  }

  const panelClass = "w-full sm:w-96 border-l border-gray-200 bg-white overflow-y-auto flex-shrink-0"

  // Popped entity from relationship graph
  if (poppedEntity !== null) {
    const { type: pType, entity: pEntity } = poppedEntity
    return (
      <div className={panelClass} aria-label="Detail panel">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3">
          <button
            onClick={() => setPoppedEntity(null)}
            className="text-xs text-blue-500 hover:text-blue-700 mb-2"
          >
            ← Back to {TYPE_LABELS[type]}
          </button>
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-medium rounded px-1.5 py-0.5 ${TYPE_BADGE_COLORS[pType]}`}>
                  {TYPE_LABELS[pType]}
                </span>
                <span className="text-xs text-gray-500">{pEntity.date}</span>
              </div>
              {(pType === "donations" || pType === "receipts") &&
                (pEntity as Donation | Receipt).name && (
                  <div className="text-base font-medium text-gray-800 truncate">
                    {(pEntity as Donation | Receipt).name}
                  </div>
                )}
              <div className="text-lg font-semibold text-gray-900">
                {fmtAmt(pEntity.net, pEntity.currency)}
              </div>
              <div className="font-mono text-xs text-gray-400 truncate mt-0.5">{pEntity.id}</div>
            </div>
            <div className="flex items-center gap-2 ml-2 shrink-0">
              <button
                onClick={() => copyToClipboard(pEntity.id)}
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
        </div>
        <div className="px-4 py-3">
          {pType === "donations" && <DonationDetail d={pEntity as Donation} />}
          {pType === "charges" && <ChargeDetail c={pEntity as Charge} />}
          {pType === "payouts" && <PayoutDetail p={pEntity as Payout} />}
          {pType === "receipts" && <ReceiptDetail r={pEntity as Receipt} />}
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-gray-400 hover:text-gray-700 select-none">
              Raw JSON
            </summary>
            <pre className="mt-2 p-2 bg-gray-50 rounded overflow-auto text-xs text-gray-700 max-h-64">
              {JSON.stringify(toFlatJson(pType, pEntity), null, 2)}
            </pre>
          </details>
        </div>
      </div>
    )
  }

  // Guessed donation found
  if (guessedDonation !== null && guessedDonation !== "none") {
    const d = guessedDonation
    return (
      <div className={panelClass} aria-label="Detail panel">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3">
          <button
            onClick={() => setGuessedDonation(null)}
            className="text-xs text-blue-500 hover:text-blue-700 mb-2"
          >
            ← Back to Receipt
          </button>
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium rounded px-1.5 py-0.5 bg-blue-100 text-blue-700">
                  Donation (suggested)
                </span>
                <span className="text-xs text-gray-500">{d.date}</span>
                <CopyButton text={d.date} />
              </div>
              {d.name && (
                <div className="flex items-center gap-1 min-w-0">
                  <div className="text-base font-medium text-gray-800 truncate">{d.name}</div>
                  <CopyButton text={d.name} />
                </div>
              )}
              <div className="flex items-center gap-1">
                <span className="text-lg font-semibold text-gray-900">
                  {fmtAmt(d.net, d.currency)}
                </span>
                <CopyButton text={fmtAmt(d.net, d.currency)} />
              </div>
              <div className="flex items-center gap-1 mt-0.5">
                <span className="font-mono text-xs text-gray-400 truncate">{d.id}</span>
                <CopyButton text={d.id} />
              </div>
            </div>
            <div className="flex items-center gap-2 ml-2 shrink-0">
              <button
                onClick={onClose}
                aria-label="Close detail panel"
                className="text-gray-400 hover:text-gray-700 text-lg leading-none"
              >
                ×
              </button>
            </div>
          </div>
        </div>
        <div className="px-4 py-3">
          <DonationDetail d={d} />
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-gray-400 hover:text-gray-700 select-none">
              Raw JSON
            </summary>
            <pre className="mt-2 p-2 bg-gray-50 rounded overflow-auto text-xs text-gray-700 max-h-64">
              {JSON.stringify(toFlatJson("donations", d), null, 2)}
            </pre>
          </details>
        </div>
      </div>
    )
  }

  // No match found
  if (guessedDonation === "none") {
    return (
      <div className={panelClass} aria-label="Detail panel">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setGuessedDonation(null)}
            className="text-xs text-blue-500 hover:text-blue-700"
          >
            ← Back to Receipt
          </button>
          <button
            onClick={onClose}
            aria-label="Close detail panel"
            className="text-gray-400 hover:text-gray-700 text-lg leading-none"
          >
            ×
          </button>
        </div>
        <div className="px-4 py-3">
          <p className="text-sm text-gray-500">No matching donation found.</p>
        </div>
      </div>
    )
  }

  // Normal view
  return (
    <div
      className={panelClass}
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
            {type === "donations" && <CopyButton text={entity.date} />}
          </div>
          {(type === "donations" || type === "receipts") &&
            (entity as Donation | Receipt).name && (
              <div className="flex items-center gap-1 min-w-0">
                <div className="text-base font-medium text-gray-800 truncate">
                  {(entity as Donation | Receipt).name}
                </div>
                {type === "donations" && <CopyButton text={(entity as Donation).name!} />}
              </div>
            )}
          <div className="flex items-center gap-1">
            <span className="text-lg font-semibold text-gray-900">
              {fmtAmt(entity.net, entity.currency)}
            </span>
            {type === "donations" && <CopyButton text={fmtAmt(entity.net, entity.currency)} />}
          </div>
          <div className="flex items-center gap-1 mt-0.5">
            <span className="font-mono text-xs text-gray-400 truncate">{entity.id}</span>
            {type === "donations" && <CopyButton text={entity.id} />}
          </div>
        </div>
        <div className="flex items-center gap-2 ml-2 shrink-0">
          {type !== "donations" && (
            <button
              onClick={() => copyToClipboard(entity.id)}
              className="text-xs text-gray-500 hover:text-gray-900 border border-gray-200 rounded px-2 py-1"
              title="Copy ID"
            >
              Copy ID
            </button>
          )}
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
        {type === "donations" && <DonationDetail d={entity as Donation} onSelectEntity={handleSelectGraphEntity} />}
        {type === "charges" && <ChargeDetail c={entity as Charge} onSelectEntity={handleSelectGraphEntity} />}
        {type === "payouts" && <PayoutDetail p={entity as Payout} onSelectEntity={handleSelectGraphEntity} />}
        {type === "receipts" && (
          <ReceiptDetail r={entity as Receipt} onFindDonation={handleFindDonation} onSelectEntity={handleSelectGraphEntity} />
        )}

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
