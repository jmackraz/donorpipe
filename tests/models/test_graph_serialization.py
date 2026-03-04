"""Tests for TransactionStore.to_graph() and from_graph() round-trips."""
import pytest
from donorpipe.models.transaction_store import TransactionStore
from donorpipe.models.transactions import Donation, Charge, Payout, Receipt

RECORD: dict = {}


def make_donation(tx_id="D1", service="donorbox", payment_service="stripe", charge_tx_id="CH1") -> Donation:
    return Donation(RECORD, "f.csv", service, tx_id, "2024-01-15", "100.00",
                    "Test User", payment_service, charge_tx_id, "General", "", "test@test.com")


def make_charge(tx_id="CH1", service="stripe", payment_service="stripe", payout_tx_id="PO1") -> Charge:
    return Charge(RECORD, "f.csv", service, tx_id, "2024-01-15", "100.00",
                  "Test User", "donation", payment_service, payout_tx_id)


def make_payout(tx_id="PO1", service="stripe") -> Payout:
    return Payout(RECORD, "f.csv", service, tx_id, "2024-01-31", "1000.00")


def make_receipt(tx_id="R1", ref_id="D1") -> Receipt:
    return Receipt(RECORD, "f.csv", "qbo", tx_id, "2024-01-15", "100.00",
                   "Test User", ref_id, "Online Donation")


def make_linked_store() -> TransactionStore:
    """Build a small store with all object refs populated."""
    store = TransactionStore([])
    donation = make_donation()
    charge = make_charge()
    payout = make_payout()
    receipt = make_receipt()

    store.add_donation(donation)
    store.add_charge(charge)
    store.add_payout(payout)
    store.add_receipt(receipt)

    # wire up object refs (normally done by associate passes)
    donation.charge = charge
    donation.receipts = [receipt]
    charge.payout = payout
    payout.charges = [charge]
    receipt.donation = donation

    return store


class TestToGraphStructure:
    def test_top_level_keys(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert set(graph.keys()) == {"donations", "charges", "payouts", "receipts"}

    def test_entity_ids_present(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert "donorbox:D1" in graph["donations"]
        assert "stripe:CH1" in graph["charges"]
        assert "stripe:PO1" in graph["payouts"]
        assert "qbo:R1" in graph["receipts"]

    def test_donation_has_charge_id(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert graph["donations"]["donorbox:D1"]["charge_id"] == "stripe:CH1"

    def test_donation_has_receipt_ids(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert graph["donations"]["donorbox:D1"]["receipt_ids"] == ["qbo:R1"]

    def test_charge_has_payout_id(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert graph["charges"]["stripe:CH1"]["payout_id"] == "stripe:PO1"

    def test_receipt_has_donation_id(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert graph["receipts"]["qbo:R1"]["donation_id"] == "donorbox:D1"

    def test_date_serialized_as_iso(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert graph["donations"]["donorbox:D1"]["date"] == "2024-01-15"

    def test_record_excluded(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert "record" not in graph["donations"]["donorbox:D1"]

    def test_filename_excluded(self):
        store = make_linked_store()
        graph = store.to_graph()
        assert "filename" not in graph["donations"]["donorbox:D1"]


class TestRoundtripDonations:
    def test_donation_scalar_fields(self):
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        d = restored.donations["donorbox:D1"]
        assert d.name == "Test User"
        assert d.email == "test@test.com"
        assert d.designation == "General"
        assert d.tx_id == "D1"
        assert d.service == "donorbox"

    def test_donation_charge_ref(self):
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        d = restored.donations["donorbox:D1"]
        assert d.charge is not None
        assert d.charge is restored.charges["stripe:CH1"]

    def test_donation_date_parsed(self):
        from datetime import date
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        assert restored.donations["donorbox:D1"].date == date(2024, 1, 15)


class TestRoundtripReceipts:
    def test_receipt_links_to_donation(self):
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        r = restored.receipts["qbo:R1"]
        assert r.donation is not None
        assert r.donation is restored.donations["donorbox:D1"]

    def test_donation_receipts_list_populated(self):
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        d = restored.donations["donorbox:D1"]
        assert len(d.receipts) == 1
        assert d.receipts[0] is restored.receipts["qbo:R1"]

    def test_discrepancies_list_preserved(self):
        store = make_linked_store()
        store.receipts["qbo:R1"].discrepancies = ["name", "net"]
        restored = TransactionStore.from_graph(store.to_graph())
        assert restored.receipts["qbo:R1"].discrepancies == ["name", "net"]

    def test_empty_discrepancies(self):
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        assert restored.receipts["qbo:R1"].discrepancies == []


class TestRoundtripPayouts:
    def test_payout_charges_list(self):
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        payout = restored.payouts["stripe:PO1"]
        assert len(payout.charges) == 1
        assert payout.charges[0] is restored.charges["stripe:CH1"]

    def test_charge_payout_ref(self):
        store = make_linked_store()
        restored = TransactionStore.from_graph(store.to_graph())
        charge = restored.charges["stripe:CH1"]
        assert charge.payout is restored.payouts["stripe:PO1"]


class TestFromGraphMissingRefs:
    def test_dangling_charge_id(self):
        store = make_linked_store()
        graph = store.to_graph()
        # remove the charge, leaving a dangling reference in donation
        del graph["charges"]["stripe:CH1"]
        restored = TransactionStore.from_graph(graph)
        assert restored.donations["donorbox:D1"].charge is None

    def test_dangling_payout_id(self):
        store = make_linked_store()
        graph = store.to_graph()
        del graph["payouts"]["stripe:PO1"]
        restored = TransactionStore.from_graph(graph)
        assert restored.charges.get("stripe:CH1") is None or \
               (restored.charges.get("stripe:CH1") is not None and
                restored.charges["stripe:CH1"].payout is None)

    def test_dangling_donation_id(self):
        store = make_linked_store()
        graph = store.to_graph()
        del graph["donations"]["donorbox:D1"]
        restored = TransactionStore.from_graph(graph)
        assert restored.receipts["qbo:R1"].donation is None


class TestAssociateChargesPayouts:
    def test_donation_charge_linked(self):
        from donorpipe.models.transaction_loader import associate_charges_payouts
        store = TransactionStore([])
        donation = make_donation()
        charge = make_charge()
        payout = make_payout()
        store.add_donation(donation)
        store.add_charge(charge)
        store.add_payout(payout)

        associate_charges_payouts(store)

        assert donation.charge is charge

    def test_charge_payout_linked(self):
        from donorpipe.models.transaction_loader import associate_charges_payouts
        store = TransactionStore([])
        donation = make_donation()
        charge = make_charge()
        payout = make_payout()
        store.add_donation(donation)
        store.add_charge(charge)
        store.add_payout(payout)

        associate_charges_payouts(store)

        assert charge.payout is payout

    def test_payout_charges_list(self):
        from donorpipe.models.transaction_loader import associate_charges_payouts
        store = TransactionStore([])
        donation = make_donation()
        charge = make_charge()
        payout = make_payout()
        store.add_donation(donation)
        store.add_charge(charge)
        store.add_payout(payout)

        associate_charges_payouts(store)

        assert payout.charges == [charge]
