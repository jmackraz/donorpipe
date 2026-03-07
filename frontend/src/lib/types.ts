export interface Transaction {
  id: string
  service: string
  tx_id: string
  date: string        // ISO 8601
  net: number
  currency: string
}

export interface RawDonation extends Transaction {
  name: string
  email: string
  designation: string
  comment: string
  payment_service: string
  charge_id: string | null
  payout_id: string | null
  receipt_ids: string[]
}

export interface RawCharge extends Transaction {
  name: string
  description: string
  payment_service: string
  payout_id: string | null
}

export interface RawPayout extends Transaction {}

export interface RawReceipt extends Transaction {
  name: string
  ref_id: string
  product: string
  item_class: string
  donation_id: string | null
  discrepancies: string[]
}

export interface EntityGraph {
  donations: Record<string, RawDonation>
  charges:   Record<string, RawCharge>
  payouts:   Record<string, RawPayout>
  receipts:  Record<string, RawReceipt>
}
