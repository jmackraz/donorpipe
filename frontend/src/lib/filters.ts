import type { Donation, Charge, Payout, Receipt } from "./graph"
import type { Filters, DateInterval } from "../hooks/useFilters"
import { computeDateRange } from "./dateRange"

function inAmountRange(net: number, min: number | null, max: number | null): boolean {
  if (min !== null && net < min) return false
  if (max !== null && net > max) return false
  return true
}

function inDateRange(date: string, dateStart: string, dateInterval: DateInterval): boolean {
  if (!dateStart) return true
  const { start, end } = computeDateRange(dateStart, dateInterval)
  return date >= start && date <= end
}

export function filterDonations(donations: Map<string, Donation>, f: Filters): Donation[] {
  const donor = f.donor.toLowerCase()
  const results: Donation[] = []

  for (const d of donations.values()) {
    if (!inAmountRange(d.net, f.amountMin, f.amountMax)) continue
    if (!inDateRange(d.date, f.dateStart, f.dateInterval)) continue
    if (f.service && d.service !== f.service) continue
    if (
      donor &&
      !d.name.toLowerCase().includes(donor) &&
      !d.id.toLowerCase().includes(donor) &&
      !(d.designation ?? "").toLowerCase().includes(donor) &&
      !(d.email ?? "").toLowerCase().includes(donor)
    )
      continue
    if (f.missing && d.receipts.length !== 0) continue
    if (f.duplicates && d.receipts.length <= 1) continue
    results.push(d)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}

export function filterCharges(charges: Map<string, Charge>, f: Filters): Charge[] {
  const results: Charge[] = []

  for (const c of charges.values()) {
    if (!inAmountRange(c.net, f.amountMin, f.amountMax)) continue
    if (!inDateRange(c.date, f.dateStart, f.dateInterval)) continue
    results.push(c)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}

export function filterPayouts(payouts: Map<string, Payout>, f: Filters): Payout[] {
  const results: Payout[] = []

  for (const p of payouts.values()) {
    if (!inAmountRange(p.net, f.amountMin, f.amountMax)) continue
    if (!inDateRange(p.date, f.dateStart, f.dateInterval)) continue
    if (f.service && p.service !== f.service) continue
    results.push(p)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}

export function filterReceipts(receipts: Map<string, Receipt>, f: Filters): Receipt[] {
  const donor = f.donor.toLowerCase()
  const results: Receipt[] = []

  for (const r of receipts.values()) {
    if (!inAmountRange(r.net, f.amountMin, f.amountMax)) continue
    if (!inDateRange(r.date, f.dateStart, f.dateInterval)) continue
    if (
      donor &&
      !r.name.toLowerCase().includes(donor) &&
      !r.id.toLowerCase().includes(donor) &&
      !(r.product ?? "").toLowerCase().includes(donor)
    )
      continue
    if (f.missing && r.donation !== null) continue
    if (f.discrepancies && r.discrepancies.length === 0) continue
    results.push(r)
  }

  return results.sort((a, b) => b.date.localeCompare(a.date))
}
