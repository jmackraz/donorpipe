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

---

## Recommendations and Serialization Design

### Known Issues in the Current Implementation

**Bug: `Donation.receipts` mutates `duplicate_receipts` on every call**

```python
@property
def receipts(self) -> list[Receipt]:
    receipts = self.duplicate_receipts or []   # NOT a copy — same list object
    if self.receipt:
        receipts.append(self.receipt)          # mutates self.duplicate_receipts in-place
    return receipts
```

When `duplicate_receipts` is non-empty and `receipt` is also set, every call appends
another copy of `receipt` into `duplicate_receipts`. In practice `receipt` is `None`
when `duplicate_receipts` is populated (see `associate_donation_receipts`), so the bug
is dormant — but the code is fragile and will misbehave if that invariant ever breaks.

**Design inconsistency: split receipt storage**

The single-receipt case (`donation.receipt`) and the multi-receipt case
(`donation.duplicate_receipts`) use separate fields, making callers reason about two
code paths. The word "duplicate" is also misleading — it implies an error rather than a
structural fact (one donation matched multiple QBO lines).

**Performance: `payout_charges()` is O(n) per call**

`payout_charges` scans every charge on every call. With large datasets and many payouts
this becomes O(p × c). A reverse index built once at association time would make each
lookup O(1).

**Performance: `associate_donation_receipts()` is O(d × r)**

The function scans all receipts for every donation. Building a `ref_id → [receipts]`
dict first reduces this to O(d + r).

**Weak typing: `receipt.discrepancies` is a space-separated string**

`"name net"` is harder to query programmatically than `["name", "net"]`. A `list[str]`
(or `set[str]`) would be cleaner and map directly to a JSON array on the front-end.

---

### Decided: Use Object References for All Relationships

The current implementation is inconsistent: Donation↔Receipt uses object references
while Donation→Charge and Charge→Payout use string ID lookups via store methods. We
have decided to extend the object-reference pattern to all relationships.

**Target entity fields** (set by a post-load association pass):

| Entity | Field | Type |
|--------|-------|------|
| `Donation` | `charge` | `Charge \| None` |
| `Donation` | `receipts` | `list[Receipt]` |
| `Charge` | `payout` | `Payout \| None` |
| `Payout` | `charges` | `list[Charge]` |
| `Receipt` | `donation` | `Donation \| None` |

The three `TransactionStore` query methods (`donation_charge`, `charge_payout`,
`payout_charges`) become redundant and should be removed. Traversal becomes:

```python
donation.charge.payout          # was: store.charge_payout(store.donation_charge(d))
payout.charges                  # was: store.payout_charges(payout)  — O(n) scan
donation.receipts               # already exists, needs cleanup (see below)
```

**Note on PayPal late-binding**: `charge.payout_tx_id` is patched mid-stream during
PayPal loading. This is fine — the association pass already runs after all files are
loaded, so the string ID is available by the time we resolve it to an object.  We should think
deeply to confirm this assumption when we solve this.

### Remaining Python-Side Improvements

1. **Unify receipt storage on `Donation`** (part of object-ref migration)
   - Replace `receipt: Receipt | None` and `duplicate_receipts: list[Receipt]` with a
     single `receipts: list[Receipt]` (always a list, 0–many elements).
   - "Has a receipt" → `len(donation.receipts) == 1`; "has duplicates" →
     `len(donation.receipts) > 1`. Remove the buggy `receipts` property.

2. **Change `receipt.discrepancies` to `list[str]`**
   - Store `[]` instead of `None` when there are none (simpler null handling).
   - `note_discrepancies` appends strings to the list instead of joining them.

3. **Optimize the association pass**
   - Build `receipts_by_ref_id: dict[str, list[Receipt]]` first (one pass), then
     iterate donations with O(1) lookups — avoids the current O(d × r) scan.

---

### Serialization Design Proposal

#### Recommended format: Normalized (flat) JSON

The entity graph has bidirectional links (`donation.receipts ↔ receipt.donation`) that
make naive JSON serialization fail with circular-reference errors. The standard solution
is a **normalized store**: each entity type lives in a flat dict keyed by `.id`;
relationships are stored as ID strings. This is the pattern used by Redux Toolkit's
entity adapters and is idiomatic for React front-ends.

```json
{
  "donations": {
    "donorbox:12345": {
      "id": "donorbox:12345",
      "service": "donorbox",
      "tx_id": "12345",
      "date": "2024-01-15",
      "net": 100.00,
      "currency": "USD",
      "name": "Jane Doe",
      "email": "jane@example.com",
      "designation": "General Fund",
      "comment": "",
      "payment_service": "stripe",
      "charge_id": "stripe:ch_abc123",
      "receipt_ids": ["qbo:INV-001"]
    }
  },
  "charges": {
    "stripe:ch_abc123": {
      "id": "stripe:ch_abc123",
      "service": "stripe",
      "tx_id": "ch_abc123",
      "date": "2024-01-15",
      "net": 97.10,
      "currency": "USD",
      "name": "Jane Doe",
      "description": "Donation",
      "payment_service": "stripe",
      "payout_id": "stripe:po_xyz789"
    }
  },
  "payouts": {
    "stripe:po_xyz789": { ... }
  },
  "receipts": {
    "qbo:INV-001": {
      "id": "qbo:INV-001",
      "service": "qbo",
      "tx_id": "INV-001",
      "date": "2024-01-20",
      "net": 100.00,
      "currency": "USD",
      "name": "Jane Doe",
      "ref_id": "12345",
      "product": "General Donation",
      "donation_id": "donorbox:12345",
      "discrepancies": []
    }
  }
}
```

Key serialization decisions:

| Field | Serialization |
|-------|--------------|
| `date` | ISO 8601 string (`date.isoformat()`) |
| `record` (raw CSV row) | **excluded** — internal/debug only |
| `filename` | **excluded** — internal; could be added for debug builds |
| Object refs | emit IDs: `"charge_id": self.charge.id if self.charge else None` |
| `receipt_ids` | `[r.id for r in self.receipts]` |
| `discrepancies` | `list[str]` — e.g. `["name", "net"]`; empty list if none |
| Missing relationships | `null` for singular, `[]` for lists |

#### Python serialization entry point

Add `TransactionStore.to_graph() -> dict` that returns the normalized structure above.
Each entity class gets a `to_dict() -> dict` method that emits only serializable fields.
The store assembles the four top-level dicts and returns the whole graph.

```python
# sketch
def to_graph(self) -> dict:
    return {
        "donations": {k: v.to_dict() for k, v in self.donations.items()},
        "charges":   {k: v.to_dict() for k, v in self.charges.items()},
        "payouts":   {k: v.to_dict() for k, v in self.payouts.items()},
        "receipts":  {k: v.to_dict() for k, v in self.receipts.items()},
    }
```

The result can be sent over HTTP as JSON or written to a file.

#### TypeScript types

```typescript
interface Transaction {
  id: string
  service: string
  tx_id: string
  date: string        // ISO 8601
  net: number
  currency: string
}

interface Donation extends Transaction {
  name: string
  email: string
  designation: string
  comment: string
  payment_service: string
  charge_id: string | null
  receipt_ids: string[]
}

interface Charge extends Transaction {
  name: string
  description: string
  payment_service: string
  payout_id: string | null
}

interface Payout extends Transaction {}

interface Receipt extends Transaction {
  name: string
  ref_id: string
  product: string
  donation_id: string | null
  discrepancies: string[]   // e.g. ["name", "net"]
}

interface EntityGraph {
  donations: Record<string, Donation>
  charges:   Record<string, Charge>
  payouts:   Record<string, Payout>
  receipts:  Record<string, Receipt>
}
```

Relationship resolution on the front-end is a simple dict lookup:

```typescript
const charge = graph.charges[donation.charge_id ?? ""]
const payout = charge ? graph.payouts[charge.payout_id ?? ""] : undefined
const receipts = donation.receipt_ids.map(id => graph.receipts[id])
```

#### Why not nested/embedded JSON?

An alternative is to embed related entities inline (e.g. embed the charge inside the
donation). This is simpler for read-only display but has two problems for this project:

1. **Data duplication**: a Payout object would be repeated inside every Charge that
   references it.
2. **Circular reference**: embedding receipts inside donations and donations inside
   receipts creates a cycle. One direction must be broken, making the schema asymmetric
   and harder to reason about.

The normalized format avoids both problems at the cost of explicit joins on the client,
which are trivial with a dict lookup.
