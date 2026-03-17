import type { EntityGraph, GraphMeta, RawDonation, RawCharge, RawPayout, RawReceipt } from "./types"

// Resolved types — object references instead of IDs
export interface Donation extends Omit<RawDonation, "charge_id" | "payout_id" | "receipt_ids"> {
  charge: Charge | null
  payout: Payout | null
  receipts: Receipt[]
}

export interface Charge extends Omit<RawCharge, "payout_id"> {
  payout: Payout | null
  donations: Donation[]
}

export interface Payout extends RawPayout {
  charges: Charge[]
}

export interface Receipt extends Omit<RawReceipt, "donation_id"> {
  donation: Donation | null
}

export interface TransactionStore {
  meta:      GraphMeta | undefined
  donations: Map<string, Donation>
  charges:   Map<string, Charge>
  payouts:   Map<string, Payout>
  receipts:  Map<string, Receipt>
}

export function fromGraph(data: EntityGraph): TransactionStore {
  // Pass 1: create all entities with unresolved refs
  const donations = new Map<string, Donation>()
  const charges = new Map<string, Charge>()
  const payouts = new Map<string, Payout>()
  const receipts = new Map<string, Receipt>()

  for (const [id, raw] of Object.entries(data.donations)) {
    const { charge_id: _charge_id, payout_id: _payout_id, receipt_ids: _receipt_ids, ...rest } = raw
    donations.set(id, { ...rest, charge: null, payout: null, receipts: [] })
  }

  for (const [id, raw] of Object.entries(data.charges)) {
    const { payout_id: _payout_id, ...rest } = raw
    charges.set(id, { ...rest, payout: null, donations: [] })
  }

  for (const [id, raw] of Object.entries(data.payouts)) {
    payouts.set(id, { ...raw, charges: [] })
  }

  for (const [id, raw] of Object.entries(data.receipts)) {
    const { donation_id: _donation_id, ...rest } = raw
    receipts.set(id, { ...rest, donation: null })
  }

  // Pass 2: link object references
  for (const [id, raw] of Object.entries(data.donations)) {
    const donation = donations.get(id)!

    if (raw.charge_id !== null) {
      const charge = charges.get(raw.charge_id) ?? null
      donation.charge = charge
      if (charge !== null) {
        charge.donations.push(donation)
      }
    }

    for (const receiptId of raw.receipt_ids) {
      const receipt = receipts.get(receiptId)
      if (receipt !== undefined) {
        donation.receipts.push(receipt)
        receipt.donation = donation
      }
    }
  }

  for (const [id, raw] of Object.entries(data.charges)) {
    const charge = charges.get(id)!

    if (raw.payout_id !== null) {
      const payout = payouts.get(raw.payout_id) ?? null
      charge.payout = payout
      if (payout !== null) {
        payout.charges.push(charge)
      }
    }
  }

  // Pass 3: propagate payout from charge to donation
  for (const donation of donations.values()) {
    donation.payout = donation.charge?.payout ?? null
  }

  return { meta: data._meta, donations, charges, payouts, receipts }
}
