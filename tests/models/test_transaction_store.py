"""Tests for donorpipe.models.transaction_store.TransactionStore."""
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


class TestTransactionStoreAddRetrieve:
    def setup_method(self):
        self.store = TransactionStore([])

    def test_add_and_retrieve_donation(self):
        d = make_donation()
        self.store.add_donation(d)
        assert "donorbox:D1" in self.store.donations

    def test_add_and_retrieve_charge(self):
        c = make_charge()
        self.store.add_charge(c)
        assert "stripe:CH1" in self.store.charges

    def test_add_and_retrieve_payout(self):
        p = make_payout()
        self.store.add_payout(p)
        assert "stripe:PO1" in self.store.payouts

    def test_add_and_retrieve_receipt(self):
        r = make_receipt()
        self.store.add_receipt(r)
        assert "qbo:R1" in self.store.receipts

    def test_duplicate_donation_prints(self, capsys):
        d = make_donation()
        self.store.add_donation(d)
        self.store.add_donation(d)
        assert "DUPLICATE" in capsys.readouterr().out


class TestTransactionStoreAssociations:
    def setup_method(self):
        self.store = TransactionStore([])
        self.charge = make_charge()
        self.payout = make_payout()
        self.store.add_charge(self.charge)
        self.store.add_payout(self.payout)

    def test_donation_charge(self):
        d = make_donation(charge_tx_id="CH1")
        self.store.add_donation(d)
        result = self.store.donation_charge(d)
        assert result is self.charge

    def test_charge_payout(self):
        result = self.store.charge_payout(self.charge)
        assert result is self.payout

    def test_payout_charges(self):
        result = self.store.payout_charges(self.payout)
        assert self.charge in result

    def test_donation_charge_none(self):
        d = make_donation(charge_tx_id="NONEXISTENT")
        self.store.add_donation(d)
        assert self.store.donation_charge(d) is None


class TestParseFilename:
    def test_donorbox(self):
        result = TransactionStore.parse_filename("DonorBox_2024.csv")
        assert result == {"type": "donorbox"}

    def test_stripe(self):
        result = TransactionStore.parse_filename("stripe_export.csv")
        assert result == {"type": "stripe"}

    def test_paypal(self):
        result = TransactionStore.parse_filename("paypal_report.csv")
        assert result == {"type": "paypal"}

    def test_qbo(self):
        result = TransactionStore.parse_filename("QBO_2024.csv")
        assert result == {"type": "qbo"}

    def test_benevity(self):
        result = TransactionStore.parse_filename("benevity_giving.csv")
        assert result == {"type": "benevity"}

    def test_unknown(self):
        result = TransactionStore.parse_filename("unknown_file.csv")
        assert result is None
