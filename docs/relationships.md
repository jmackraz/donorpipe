# Entity Relationships

## Entities

| Entity | Source | Key Fields |
|--------|--------|------------|
| `Transaction` | base class | `record`, `filename`, `service`, `tx_id`, `date`, `net`, `currency` |
| `Donation` | DonorBox, PayPal (Mass Pay), Benevity | `name`, `email`, `payment_service`, `charge_tx_id`, `designation`, `comment` |
| `Charge` | Stripe, PayPal, Benevity (synthesized) | `name`, `description`, `payment_service`, `payout_tx_id` |
| `Payout` | Stripe, PayPal, Benevity (synthesized) | (base fields only) |
| `Receipt` | QBO (QuickBooks) | `name`, `ref_id`, `product` |

All entities have a computed `.id` property in the form `"service:tx_id"`.

---

## Relationships

### Load-Time (stored references in entity fields)

These references are stored as plain string IDs at load time. They allow lookup into `TransactionStore` dicts but do not create direct object links.

**Donation → Charge**
- `donation.charge_tx_id` — the `tx_id` of the charge (string, may be `None`)
- `donation.payment_service` — the service that processed the charge (e.g. `"stripe"`, `"paypal"`, `"benevity"`)
- Computed: `donation.charge_id` → `f"{payment_service}:{charge_tx_id}"` (matches `charge.id`)

**Charge → Payout**
- `charge.payout_tx_id` — the `tx_id` of the payout (string, may be `None`)
- `charge.payment_service` — the service that issued the payout
- Computed: `charge.payout_id` → `f"{payment_service}:{payout_tx_id}"` (matches `payout.id`)

**Receipt → Donation (matching key only)**
- `receipt.ref_id` — holds the donation's `tx_id` (not a direct object link); used for matching in `associate_donation_receipts`

---

### Runtime Links (set by `associate_donation_receipts`)

These bidirectional object links are established after all files are loaded.

**Matching logic:** a receipt matches a donation when `receipt.ref_id == donation.tx_id`.

| Case | Donation side | Receipt side |
|------|--------------|--------------|
| Exactly one receipt | `donation.receipt = rcpt` (one-to-one) | `rcpt.donation = donation` |
| Multiple receipts | `donation.duplicate_receipts = [rcpt, ...]` | each `rcpt.donation = donation` |
| No receipts | no link set | no link set |

Helper property on `Donation`:
- `donation.receipts` → combined list: `duplicate_receipts + [receipt]` (all associated receipts)

---

### Runtime Annotations (set by `note_discrepancies`)

Must be called after `associate_donation_receipts`.

- `receipt.discrepancies` — space-separated string listing fields where the receipt differs from its linked donation. Possible tokens: `name`, `net`, `date`. `None` if no discrepancies.

Example: `"name net"` means both `receipt.name != donation.name` and `receipt.net != donation.net`.

---

## Query Methods (`TransactionStore`)

These methods resolve load-time ID references to live objects.

| Method | Input | Output | Notes |
|--------|-------|--------|-------|
| `donation_charge(donation)` | `Donation \| None` | `Charge \| None` | Looks up `donation.charge_id` in `self.charges` |
| `charge_payout(charge)` | `Charge \| None` | `Payout \| None` | Looks up `charge.payout_id` in `self.payouts` |
| `payout_charges(payout)` | `Payout` | `list[Charge]` | Scans all charges where `charge.payout_id == payout.id` |

---

## Full Relationship Chain

```
Donation  ──charge_tx_id/payment_service──►  Charge  ──payout_tx_id/payment_service──►  Payout
   │  ▲                                                                                      │
   │  └── receipt.donation (runtime)                                          (payout_charges reverses this)
   │
   └──► Receipt  (via donation.receipt or donation.duplicate_receipts)
          └── receipt.discrepancies  (annotation: "name net date" mismatches)
```
