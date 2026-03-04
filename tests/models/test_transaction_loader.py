"""Integration tests: load real testdata and verify basic counts and associations."""
import os
import pytest
from donorpipe.models.transaction_loader import (
    TransactionLoader,
    associate_donation_receipts,
    note_discrepancies,
)
from donorpipe.models.transaction_store import TransactionStore

TESTDATA = os.path.join(os.path.dirname(__file__), "..", "..", "testdata")


@pytest.fixture(scope="module")
def tx_store():
    loader = TransactionLoader([], ["Stripe", "DonorBox", "QBO"])
    env_backup = os.environ.get("OSF_EXPORTS")
    os.environ["OSF_EXPORTS"] = TESTDATA
    store = loader.load()
    if env_backup is None:
        os.environ.pop("OSF_EXPORTS", None)
    else:
        os.environ["OSF_EXPORTS"] = env_backup
    return store


class TestTransactionLoaderIntegration:
    def test_donations_loaded(self, tx_store):
        assert len(tx_store.donations) > 0

    def test_receipts_loaded(self, tx_store):
        assert len(tx_store.receipts) > 0

    def test_charges_loaded(self, tx_store):
        assert len(tx_store.charges) > 0

    def test_payouts_loaded(self, tx_store):
        assert len(tx_store.payouts) > 0

    def test_some_donations_linked_to_receipts(self, tx_store):
        linked = [d for d in tx_store.donations.values() if d.receipt is not None]
        assert len(linked) > 0

    def test_some_receipts_linked_to_donations(self, tx_store):
        linked = [r for r in tx_store.receipts.values() if r.donation is not None]
        assert len(linked) > 0


class TestAssociateDonationReceipts:
    def test_links_donation_and_receipt(self):
        from donorpipe.models.transactions import Donation, Receipt

        RECORD: dict = {}
        store = TransactionStore([])
        d = Donation(RECORD, "f.csv", "donorbox", "DREF1", "2024-01-15", "100.00",
                     "Alice", "stripe", "CH1", "General", "", "alice@test.com")
        r = Receipt(RECORD, "f.csv", "qbo", "R1", "2024-01-15", "100.00",
                    "Alice", ref_id="DREF1", product="Online")
        store.add_donation(d)
        store.add_receipt(r)

        associate_donation_receipts(store)

        assert d.receipt is r
        assert r.donation is d

    def test_no_match_leaves_unlinked(self):
        from donorpipe.models.transactions import Donation, Receipt

        RECORD: dict = {}
        store = TransactionStore([])
        d = Donation(RECORD, "f.csv", "donorbox", "DREF2", "2024-01-15", "100.00",
                     "Bob", "stripe", "CH2", "General", "", "bob@test.com")
        r = Receipt(RECORD, "f.csv", "qbo", "R2", "2024-01-15", "100.00",
                    "Bob", ref_id="NOMATCH", product="Online")
        store.add_donation(d)
        store.add_receipt(r)

        associate_donation_receipts(store)

        assert d.receipt is None
        assert r.donation is None


class TestNoteDiscrepancies:
    def test_discrepancy_detected_on_name_mismatch(self):
        from donorpipe.models.transactions import Donation, Receipt

        RECORD: dict = {}
        store = TransactionStore([])
        d = Donation(RECORD, "f.csv", "donorbox", "DREF3", "2024-01-15", "100.00",
                     "Alice", "stripe", "CH3", "General", "", "alice@test.com")
        r = Receipt(RECORD, "f.csv", "qbo", "R3", "2024-01-15", "100.00",
                    "Different Name", ref_id="DREF3", product="Online")
        store.add_donation(d)
        store.add_receipt(r)

        associate_donation_receipts(store)
        note_discrepancies(store)

        assert r.discrepancies is not None
        assert "name" in r.discrepancies

    def test_no_discrepancy_when_matching(self):
        from donorpipe.models.transactions import Donation, Receipt

        RECORD: dict = {}
        store = TransactionStore([])
        d = Donation(RECORD, "f.csv", "donorbox", "DREF4", "2024-01-15", "100.00",
                     "Alice", "stripe", "CH4", "General", "", "alice@test.com")
        r = Receipt(RECORD, "f.csv", "qbo", "R4", "2024-01-15", "100.00",
                    "Alice", ref_id="DREF4", product="Online")
        store.add_donation(d)
        store.add_receipt(r)

        associate_donation_receipts(store)
        note_discrepancies(store)

        assert r.discrepancies is None
