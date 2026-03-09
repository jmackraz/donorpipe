import { describe, test, expect } from "bun:test"
import { findBestDonation } from "../src/lib/matching"
import type { Donation, Receipt } from "../src/lib/graph"

function makeDonation(overrides: Partial<Donation> & { id: string }): Donation {
  return {
    service: "Stripe",
    tx_id: `tx_${overrides.id}`,
    date: "2024-03-15",
    net: 100,
    currency: "usd",
    name: "Donor A",
    email: "",
    designation: "",
    comment: "",
    payment_service: "",
    charge: null,
    payout: null,
    receipts: [],
    ...overrides,
  }
}

function makeReceipt(overrides: Partial<Receipt> & { id: string }): Receipt {
  return {
    service: "QBO",
    tx_id: `qtx_${overrides.id}`,
    date: "2024-03-15",
    net: 100,
    currency: "usd",
    name: "Donor A",
    ref_id: "",
    product: "Online Donation",
    item_class: "",
    donation: null,
    discrepancies: [],
    ...overrides,
  }
}

describe("findBestDonation", () => {
  test("returns null when no donations", () => {
    const r = makeReceipt({ id: "r1" })
    expect(findBestDonation(r, new Map())).toBeNull()
  })

  test("returns null when all donations have receipts", () => {
    const r = makeReceipt({ id: "r1" })
    const d = makeDonation({ id: "d1", receipts: [r] })
    expect(findBestDonation(r, new Map([["d1", d]]))).toBeNull()
  })

  test("returns null when no donations in the same week", () => {
    const r = makeReceipt({ id: "r1", date: "2024-03-15" })
    const d = makeDonation({ id: "d1", date: "2024-03-01" })
    expect(findBestDonation(r, new Map([["d1", d]]))).toBeNull()
  })

  test("returns null when amount is out of range (>10% off)", () => {
    const r = makeReceipt({ id: "r1", net: 100 })
    const d = makeDonation({ id: "d1", net: 80 }) // 20% off
    expect(findBestDonation(r, new Map([["d1", d]]))).toBeNull()
  })

  test("matches donation within 10% amount range and same week", () => {
    const r = makeReceipt({ id: "r1", net: 100, date: "2024-03-15" })
    const d = makeDonation({ id: "d1", net: 95, date: "2024-03-13" }) // same week (Mon–Sun)
    expect(findBestDonation(r, new Map([["d1", d]]))).toBe(d)
  })

  test("picks closest net amount among multiple candidates", () => {
    const r = makeReceipt({ id: "r1", net: 100, date: "2024-03-15" })
    const d1 = makeDonation({ id: "d1", net: 92, date: "2024-03-13" })
    const d2 = makeDonation({ id: "d2", net: 99, date: "2024-03-14" })
    const d3 = makeDonation({ id: "d3", net: 105, date: "2024-03-15" })
    const store = new Map([["d1", d1], ["d2", d2], ["d3", d3]])
    expect(findBestDonation(r, store)).toBe(d2)
  })

  test("ignores donations that already have receipts", () => {
    const r = makeReceipt({ id: "r1", net: 100, date: "2024-03-15" })
    const dummy = makeReceipt({ id: "r2" })
    const d1 = makeDonation({ id: "d1", net: 100, date: "2024-03-15", receipts: [dummy] })
    const d2 = makeDonation({ id: "d2", net: 98, date: "2024-03-15" })
    const store = new Map([["d1", d1], ["d2", d2]])
    expect(findBestDonation(r, store)).toBe(d2)
  })

  test("week boundary: receipt on Sunday picks donation from Monday that week", () => {
    // 2024-03-17 is a Sunday; the Mon–Sun week is 2024-03-11 to 2024-03-17
    const r = makeReceipt({ id: "r1", date: "2024-03-17", net: 50 })
    const d = makeDonation({ id: "d1", date: "2024-03-11", net: 50 }) // Monday of that week
    expect(findBestDonation(r, new Map([["d1", d]]))).toBe(d)
  })

  test("week boundary: donation one day outside week is not matched", () => {
    // 2024-03-17 is a Sunday; the prior week ends 2024-03-10
    const r = makeReceipt({ id: "r1", date: "2024-03-17", net: 50 })
    const d = makeDonation({ id: "d1", date: "2024-03-10", net: 50 }) // day before week start
    expect(findBestDonation(r, new Map([["d1", d]]))).toBeNull()
  })
})
