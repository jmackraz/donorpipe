import type { Donation, Charge, Payout, Receipt } from "./graph"
import type { Filters } from "../hooks/useFilters"

function inDateRange(date: string, from: string, to: string): boolean {
  return date >= from && date <= to
}

function inAmountRange(net: number, min: number | null, max: number | null): boolean {
  // Amounts are stored as integers (cents/basis points); filters are in dollars
  if (min !== null && net < min * 100) return false
  if (max !== null && net > max * 100) return false
  return true
}

export function filterDonations(donations: Map<string, Donation>, f: Filters): Donation[] {
  const text = f.text.toLowerCase()
  const results: Donation[] = []

  for (const d of donations.values()) {
    if (!inDateRange(d.date, f.dateFrom, f.dateTo)) continue
    if (!inAmountRange(d.net, f.amountMin, f.amountMax)) continue
    if (
      text &&
      !d.name.toLowerCase().includes(text) &&
      !d.id.toLowerCase().includes(text) &&
      !(d.designation ?? "").toLowerCase().includes(text) &&
      !(d.email ?? "").toLowerCase().includes(text)
    )
      continue
    if (f.donationMatch === "has_charge" && d.charge === null) continue
    if (f.donationMatch === "has_receipt" && d.receipts.length === 0) continue
    if (f.donationMatch === "unmatched" && (d.charge !== null || d.receipts.length > 0)) continue
    results.push(d)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}

export function filterCharges(charges: Map<string, Charge>, f: Filters): Charge[] {
  const text = f.text.toLowerCase()
  const results: Charge[] = []

  for (const c of charges.values()) {
    if (!inDateRange(c.date, f.dateFrom, f.dateTo)) continue
    if (!inAmountRange(c.net, f.amountMin, f.amountMax)) continue
    if (
      text &&
      !c.name.toLowerCase().includes(text) &&
      !c.id.toLowerCase().includes(text) &&
      !(c.description ?? "").toLowerCase().includes(text)
    )
      continue
    results.push(c)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}

export function filterPayouts(payouts: Map<string, Payout>, f: Filters): Payout[] {
  const results: Payout[] = []

  for (const p of payouts.values()) {
    if (!inDateRange(p.date, f.dateFrom, f.dateTo)) continue
    if (!inAmountRange(p.net, f.amountMin, f.amountMax)) continue
    results.push(p)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}

export function filterReceipts(receipts: Map<string, Receipt>, f: Filters): Receipt[] {
  const text = f.text.toLowerCase()
  const results: Receipt[] = []

  for (const r of receipts.values()) {
    if (!inDateRange(r.date, f.dateFrom, f.dateTo)) continue
    if (!inAmountRange(r.net, f.amountMin, f.amountMax)) continue
    if (
      text &&
      !r.name.toLowerCase().includes(text) &&
      !r.id.toLowerCase().includes(text) &&
      !(r.product ?? "").toLowerCase().includes(text)
    )
      continue
    results.push(r)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}
