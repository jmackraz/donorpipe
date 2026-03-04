import { describe, test, expect } from "bun:test"
import { fromGraph } from "../src/lib/graph"
import type { EntityGraph } from "../src/lib/types"

const emptyGraph: EntityGraph = {
  donations: {},
  charges: {},
  payouts: {},
  receipts: {},
}

describe("fromGraph", () => {
  test("empty graph returns empty Maps", () => {
    const store = fromGraph(emptyGraph)
    expect(store.donations.size).toBe(0)
    expect(store.charges.size).toBe(0)
    expect(store.payouts.size).toBe(0)
    expect(store.receipts.size).toBe(0)
  })

  test("single donation deserializes correctly", () => {
    const graph: EntityGraph = {
      ...emptyGraph,
      donations: {
        "donorbox:100": {
          id: "donorbox:100",
          service: "donorbox",
          tx_id: "100",
          date: "2024-01-15",
          net: 100.00,
          currency: "USD",
          name: "Jane Doe",
          email: "jane@example.com",
          designation: "General Fund",
          comment: "",
          payment_service: "stripe",
          charge_id: null,
          receipt_ids: [],
        },
      },
    }
    const store = fromGraph(graph)
    const donation = store.donations.get("donorbox:100")!
    expect(donation.id).toBe("donorbox:100")
    expect(donation.service).toBe("donorbox")
    expect(donation.tx_id).toBe("100")
    expect(donation.date).toBe("2024-01-15")
    expect(donation.net).toBe(100.00)
    expect(donation.currency).toBe("USD")
    expect(donation.name).toBe("Jane Doe")
    expect(donation.email).toBe("jane@example.com")
    expect(donation.designation).toBe("General Fund")
    expect(donation.comment).toBe("")
    expect(donation.payment_service).toBe("stripe")
    expect(donation.charge).toBeNull()
    expect(donation.receipts).toEqual([])
  })

  test("single charge deserializes correctly", () => {
    const graph: EntityGraph = {
      ...emptyGraph,
      charges: {
        "stripe:ch_abc": {
          id: "stripe:ch_abc",
          service: "stripe",
          tx_id: "ch_abc",
          date: "2024-01-15",
          net: 97.10,
          currency: "USD",
          name: "Jane Doe",
          description: "Donation",
          payment_service: "stripe",
          payout_id: null,
        },
      },
    }
    const store = fromGraph(graph)
    const charge = store.charges.get("stripe:ch_abc")!
    expect(charge.id).toBe("stripe:ch_abc")
    expect(charge.net).toBe(97.10)
    expect(charge.payout).toBeNull()
    expect(charge.donations).toEqual([])
  })

  test("single payout deserializes correctly", () => {
    const graph: EntityGraph = {
      ...emptyGraph,
      payouts: {
        "stripe:po_xyz": {
          id: "stripe:po_xyz",
          service: "stripe",
          tx_id: "po_xyz",
          date: "2024-01-20",
          net: 485.50,
          currency: "USD",
        },
      },
    }
    const store = fromGraph(graph)
    const payout = store.payouts.get("stripe:po_xyz")!
    expect(payout.id).toBe("stripe:po_xyz")
    expect(payout.net).toBe(485.50)
    expect(payout.charges).toEqual([])
  })

  test("single receipt deserializes correctly", () => {
    const graph: EntityGraph = {
      ...emptyGraph,
      receipts: {
        "qbo:INV-001": {
          id: "qbo:INV-001",
          service: "qbo",
          tx_id: "INV-001",
          date: "2024-01-20",
          net: 100.00,
          currency: "USD",
          name: "Jane Doe",
          ref_id: "100",
          product: "General Donation",
          donation_id: null,
          discrepancies: [],
        },
      },
    }
    const store = fromGraph(graph)
    const receipt = store.receipts.get("qbo:INV-001")!
    expect(receipt.id).toBe("qbo:INV-001")
    expect(receipt.ref_id).toBe("100")
    expect(receipt.product).toBe("General Donation")
    expect(receipt.donation).toBeNull()
    expect(receipt.discrepancies).toEqual([])
  })

  test("linked donation → charge → payout resolves object references", () => {
    const graph: EntityGraph = {
      donations: {
        "donorbox:100": {
          id: "donorbox:100",
          service: "donorbox",
          tx_id: "100",
          date: "2024-01-15",
          net: 100.00,
          currency: "USD",
          name: "Jane Doe",
          email: "jane@example.com",
          designation: "General Fund",
          comment: "",
          payment_service: "stripe",
          charge_id: "stripe:ch_abc",
          receipt_ids: [],
        },
      },
      charges: {
        "stripe:ch_abc": {
          id: "stripe:ch_abc",
          service: "stripe",
          tx_id: "ch_abc",
          date: "2024-01-15",
          net: 97.10,
          currency: "USD",
          name: "Jane Doe",
          description: "Donation",
          payment_service: "stripe",
          payout_id: "stripe:po_xyz",
        },
      },
      payouts: {
        "stripe:po_xyz": {
          id: "stripe:po_xyz",
          service: "stripe",
          tx_id: "po_xyz",
          date: "2024-01-20",
          net: 485.50,
          currency: "USD",
        },
      },
      receipts: {},
    }
    const store = fromGraph(graph)

    const donation = store.donations.get("donorbox:100")!
    const charge = store.charges.get("stripe:ch_abc")!
    const payout = store.payouts.get("stripe:po_xyz")!

    // Forward references
    expect(donation.charge).toBe(charge)
    expect(charge.payout).toBe(payout)

    // Reverse references
    expect(charge.donations).toContain(donation)
    expect(payout.charges).toContain(charge)
  })

  test("donation with receipts — forward and back-references set", () => {
    const graph: EntityGraph = {
      donations: {
        "donorbox:100": {
          id: "donorbox:100",
          service: "donorbox",
          tx_id: "100",
          date: "2024-01-15",
          net: 100.00,
          currency: "USD",
          name: "Jane Doe",
          email: "jane@example.com",
          designation: "General Fund",
          comment: "",
          payment_service: "stripe",
          charge_id: null,
          receipt_ids: ["qbo:INV-001", "qbo:INV-002"],
        },
      },
      charges: {},
      payouts: {},
      receipts: {
        "qbo:INV-001": {
          id: "qbo:INV-001",
          service: "qbo",
          tx_id: "INV-001",
          date: "2024-01-20",
          net: 100.00,
          currency: "USD",
          name: "Jane Doe",
          ref_id: "100",
          product: "General Donation",
          donation_id: "donorbox:100",
          discrepancies: [],
        },
        "qbo:INV-002": {
          id: "qbo:INV-002",
          service: "qbo",
          tx_id: "INV-002",
          date: "2024-01-21",
          net: 100.00,
          currency: "USD",
          name: "Jane Doe",
          ref_id: "100",
          product: "General Donation",
          donation_id: "donorbox:100",
          discrepancies: [],
        },
      },
    }
    const store = fromGraph(graph)

    const donation = store.donations.get("donorbox:100")!
    const receipt1 = store.receipts.get("qbo:INV-001")!
    const receipt2 = store.receipts.get("qbo:INV-002")!

    expect(donation.receipts).toHaveLength(2)
    expect(donation.receipts).toContain(receipt1)
    expect(donation.receipts).toContain(receipt2)
    expect(receipt1.donation).toBe(donation)
    expect(receipt2.donation).toBe(donation)
  })

  test("null charge_id leaves donation.charge as null", () => {
    const graph: EntityGraph = {
      ...emptyGraph,
      donations: {
        "donorbox:200": {
          id: "donorbox:200",
          service: "donorbox",
          tx_id: "200",
          date: "2024-02-01",
          net: 50.00,
          currency: "USD",
          name: "Bob Smith",
          email: "bob@example.com",
          designation: "",
          comment: "",
          payment_service: "paypal",
          charge_id: null,
          receipt_ids: [],
        },
      },
    }
    const store = fromGraph(graph)
    const donation = store.donations.get("donorbox:200")!
    expect(donation.charge).toBeNull()
  })

  test("receipt discrepancies array is preserved", () => {
    const graph: EntityGraph = {
      ...emptyGraph,
      receipts: {
        "qbo:INV-003": {
          id: "qbo:INV-003",
          service: "qbo",
          tx_id: "INV-003",
          date: "2024-03-01",
          net: 95.00,
          currency: "USD",
          name: "Wrong Name",
          ref_id: "300",
          product: "General Donation",
          donation_id: null,
          discrepancies: ["name", "net"],
        },
      },
    }
    const store = fromGraph(graph)
    const receipt = store.receipts.get("qbo:INV-003")!
    expect(receipt.discrepancies).toEqual(["name", "net"])
  })
})
