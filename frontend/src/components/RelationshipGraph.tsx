import type { Donation, Charge, Payout, Receipt } from "../lib/graph"

type AnyEntity = Donation | Charge | Payout | Receipt

interface CanonicalEntry {
  donation: Donation | null
  receipts: Receipt[]
}

interface CanonicalForm {
  payout: Payout | null
  entries: CanonicalEntry[]
}

function isPayout(e: AnyEntity): e is Payout {
  return "charges" in e
}

function isCharge(e: AnyEntity): e is Charge {
  return "donations" in e
}

function isReceipt(e: AnyEntity): e is Receipt {
  return "donation" in e
}

function donationsToEntries(donations: Donation[]): CanonicalEntry[] {
  if (donations.length === 0) return [{ donation: null, receipts: [] }]
  return donations.map((d) => ({ donation: d, receipts: d.receipts }))
}

function fromDonation(donation: Donation): CanonicalForm {
  const payout = donation.payout
  let donations: Donation[]
  if (payout) {
    donations = payout.charges.flatMap((c) => c.donations)
  } else if (donation.charge) {
    donations = donation.charge.donations
  } else {
    donations = [donation]
  }
  return { payout, entries: donationsToEntries(donations) }
}

function buildCanonicalForm(entity: AnyEntity): CanonicalForm {
  if (isPayout(entity)) {
    const donations = entity.charges.flatMap((c) => c.donations)
    return { payout: entity, entries: donationsToEntries(donations) }
  }
  if (isCharge(entity)) {
    const payout = entity.payout
    const donations = payout ? payout.charges.flatMap((c) => c.donations) : entity.donations
    return { payout, entries: donationsToEntries(donations) }
  }
  if (isReceipt(entity)) {
    if (entity.donation) return fromDonation(entity.donation)
    return { payout: null, entries: [{ donation: null, receipts: [entity] }] }
  }
  return fromDonation(entity)
}

function fmtAmt(net: number, currency: string): string {
  return `${(net / 100).toFixed(2)} ${currency.toUpperCase()}`
}

function PayoutNode({ payout }: { payout: Payout | null }) {
  if (!payout) {
    return <div className="text-gray-400 italic text-sm">— No payout —</div>
  }
  return (
    <div className="text-sm">
      <span className="text-xs text-gray-400 mr-2">Payout</span>
      <span className="font-mono text-xs text-gray-600 mr-2">{payout.id}</span>
      <span className="text-gray-900">
        {fmtAmt(payout.net, payout.currency)} · {payout.date}
      </span>
    </div>
  )
}

function DonationNode({ donation }: { donation: Donation | null }) {
  if (!donation) {
    return <div className="text-gray-400 italic text-sm ml-4">— No donation —</div>
  }
  return (
    <div className="text-sm ml-4">
      <span className="text-xs text-gray-400 mr-2">Donation</span>
      <span className="text-gray-900">{donation.name || "—"}</span>
      <span className="text-gray-500 mx-1">·</span>
      <span className="text-gray-900">{fmtAmt(donation.net, donation.currency)}</span>
      <span className="text-gray-500 mx-1">·</span>
      <span className="text-gray-900">{donation.date}</span>
    </div>
  )
}

function ReceiptNode({ receipt }: { receipt: Receipt }) {
  return (
    <div className="text-sm">
      <span className="text-xs text-gray-400 mr-2">Receipt</span>
      <span className="font-mono text-xs text-gray-600 mr-2">{receipt.id}</span>
      <span className={`mr-2 ${receipt.item_class ? "text-gray-700" : "text-gray-400 italic"}`}>
        {receipt.item_class ?? "no class"}
      </span>
      <span className="text-gray-900">
        {fmtAmt(receipt.net, receipt.currency)} · {receipt.date}
      </span>
      {receipt.discrepancies.length > 0 && (
        <span className="text-amber-600 text-xs ml-2">⚠ {receipt.discrepancies.join(" ")}</span>
      )}
    </div>
  )
}

function ReceiptSection({ receipts }: { receipts: Receipt[] }) {
  if (receipts.length === 0) {
    return <div className="text-gray-400 italic text-sm ml-8">— No receipt —</div>
  }
  if (receipts.length === 1) {
    return (
      <div className="ml-8">
        <ReceiptNode receipt={receipts[0]!} />
      </div>
    )
  }
  return (
    <div className="ml-8 space-y-1">
      {receipts.map((r) => (
        <div key={r.id} className="border border-amber-200 rounded px-2 py-1 bg-amber-50">
          <ReceiptNode receipt={r} />
        </div>
      ))}
    </div>
  )
}

interface Props {
  entity: Donation | Charge | Payout | Receipt
}

export default function RelationshipGraph({ entity }: Props) {
  const form = buildCanonicalForm(entity)
  return (
    <section className="mb-4">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Relationships
      </h3>
      <div className="space-y-2">
        <PayoutNode payout={form.payout} />
        {form.entries.map((entry, i) => (
          <div key={entry.donation?.id ?? `placeholder-${i}`} className="space-y-1">
            <DonationNode donation={entry.donation} />
            <ReceiptSection receipts={entry.receipts} />
          </div>
        ))}
      </div>
    </section>
  )
}
