import type { Donation, Receipt } from "./graph"
import { computeDateRange } from "./dateRange"

export function findBestDonation(
  receipt: Receipt,
  donations: Map<string, Donation>,
): Donation | null {
  const { start, end } = computeDateRange(receipt.date, "week")
  const minNet = receipt.net * 0.9
  const maxNet = receipt.net * 1.1

  const candidates: Donation[] = []
  for (const d of donations.values()) {
    if (d.receipts.length !== 0) continue
    if (d.net < minNet || d.net > maxNet) continue
    if (d.date < start || d.date > end) continue
    candidates.push(d)
  }

  if (candidates.length === 0) return null

  candidates.sort((a, b) => Math.abs(a.net - receipt.net) - Math.abs(b.net - receipt.net))
  return candidates[0] ?? null
}
