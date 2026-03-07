import { useEffect, useCallback } from "react"
import type { Donation, Charge, Payout, Receipt } from "../lib/graph"
import type { EntityType } from "../hooks/useFilters"

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

      <section className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Relationships
        </h3>
        {d.payout ? (
          <div className="border border-gray-200 rounded p-2 text-sm mb-2">
            <div className="text-xs text-gray-400 mb-0.5">Payout</div>
            <div className="font-mono text-xs text-gray-600">{d.payout.id}</div>
            <div className="text-gray-900">
              {fmtAmt(d.payout.net, d.payout.currency)} · {d.payout.date}
            </div>
            {d.charge && (
              <div className="mt-1.5 pl-3 border-l-2 border-gray-200">
                <div className="text-xs text-gray-400 mb-0.5">Charge</div>
                <div className="font-mono text-xs text-gray-600">{d.charge.id}</div>
                <div className="text-gray-900">
                  {fmtAmt(d.charge.net, d.charge.currency)} · {d.charge.date}
                </div>
              </div>
            )}
          </div>
        ) : d.charge ? (
          <div className="border border-gray-200 rounded p-2 text-sm mb-2">
            <div className="text-xs text-gray-400 mb-0.5">Charge</div>
            <div className="font-mono text-xs text-gray-600">{d.charge.id}</div>
            <div className="text-gray-900">
              {fmtAmt(d.charge.net, d.charge.currency)} · {d.charge.date}
            </div>
            <p className="text-xs text-gray-400 mt-1">Not yet paid out.</p>
          </div>
        ) : (
          <p className="text-sm text-gray-400 mb-2">No charge linked.</p>
        )}

        {d.receipts.length > 0 && (
          <div>
            <div className="text-xs text-gray-400 mb-1">
              Receipts ({d.receipts.length})
            </div>
            {d.receipts.map((r) => (
              <div
                key={r.id}
                className="border border-gray-200 rounded p-2 text-sm mb-1"
              >
                <div className="font-mono text-xs text-gray-600">{r.id}</div>
                <div className="text-gray-900">
                  {fmtAmt(r.net, r.currency)} · {r.date}
                  {r.product ? ` · ${r.product}` : ""}
                </div>
                {r.discrepancies.length > 0 && (
                  <div className="text-amber-600 text-xs mt-0.5">
                    ⚠ {r.discrepancies.join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
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

      <section className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Relationships
        </h3>
        {c.payout ? (
          <div className="border border-gray-200 rounded p-2 text-sm">
            <div className="text-xs text-gray-400 mb-0.5">Payout</div>
            <div className="font-mono text-xs text-gray-600">{c.payout.id}</div>
            <div className="text-gray-900">
              {fmtAmt(c.payout.net, c.payout.currency)} · {c.payout.date}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">Not yet paid out.</p>
        )}
        {c.donations.length > 0 && (
          <div className="mt-2">
            <div className="text-xs text-gray-400 mb-1">Donations ({c.donations.length})</div>
            {c.donations.map((d) => (
              <div key={d.id} className="border border-gray-200 rounded p-2 text-sm mb-1">
                <div className="font-mono text-xs text-gray-600">{d.id}</div>
                <div className="text-gray-900">
                  {d.name || "—"} · {fmtAmt(d.net, d.currency)} · {d.date}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  )
}

function PayoutDetail({ p }: { p: Payout }) {
  return (
    <section className="mb-4">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
        Charges ({p.charges.length})
      </h3>
      {p.charges.length === 0 ? (
        <p className="text-sm text-gray-400">No charges.</p>
      ) : (
        p.charges.map((c) => (
          <div key={c.id} className="border border-gray-200 rounded p-2 text-sm mb-1">
            <div className="font-mono text-xs text-gray-600">{c.id}</div>
            <div className="text-gray-900">
              {c.name || "—"} · {fmtAmt(c.net, c.currency)} · {c.date}
            </div>
          </div>
        ))
      )}
    </section>
  )
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

      <section className="mb-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Matched Donation
        </h3>
        {r.donation ? (
          <div className="border border-gray-200 rounded p-2 text-sm">
            <div className="font-mono text-xs text-gray-600">{r.donation.id}</div>
            <div className="text-gray-900">
              {r.donation.name || "—"} · {fmtAmt(r.donation.net, r.donation.currency)} ·{" "}
              {r.donation.date}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No donation matched.</p>
        )}
      </section>
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
