"""Tests for donorpipe.models.transactions."""
import pytest
from datetime import date

from donorpipe.models.transactions import Transaction, Donation, Charge, Payout, Receipt, payment_type

RECORD: dict = {}


class TestPaymentType:
    def test_stripe(self):
        assert payment_type("stripe") == "credit card"

    def test_paypal(self):
        assert payment_type("paypal") == "paypal"

    def test_other(self):
        assert payment_type("benevity") == "other: benevity"


class TestTransaction:
    def _make(self, **kwargs):
        defaults = dict(record=RECORD, filename="f.csv", service="stripe",
                        tx_id="TX1", date="2024-03-15", net="100.00")
        defaults.update(kwargs)
        return Transaction(**defaults)

    def test_date_parsed(self):
        t = self._make(date="2024-03-15")
        assert t.date == date(2024, 3, 15)

    def test_net_parsed(self):
        t = self._make(net="1,234.56")
        assert t.net == pytest.approx(1234.56)

    def test_id(self):
        t = self._make(service="stripe", tx_id="abc")
        assert t.id == "stripe:abc"

    def test_str_contains_service(self):
        t = self._make()
        assert "stripe" in str(t)

    def test_default_currency(self):
        t = self._make()
        assert t.currency == "USD"


class TestDonation:
    def _make(self, **kwargs):
        defaults = dict(record=RECORD, filename="f.csv", service="donorbox",
                        tx_id="D1", date="2024-06-01", net="50.00",
                        name="Alice Smith", payment_service="stripe",
                        charge_tx_id="CH1", designation="General",
                        comment="", email="alice@example.com")
        defaults.update(kwargs)
        return Donation(**defaults)

    def test_charge_id(self):
        d = self._make(payment_service="stripe", charge_tx_id="CH1")
        assert d.charge_id == "stripe:CH1"

    def test_receipts_empty_by_default(self):
        d = self._make()
        assert d.receipts == []

    def test_receipt_linked(self):
        d = self._make()
        r = Receipt(RECORD, "f.csv", "qbo", "R1", "2024-06-01", "50.00",
                    "Alice Smith", ref_id="D1", product="Online")
        d.receipts.append(r)
        assert r in d.receipts

    def test_str_contains_donation(self):
        d = self._make()
        assert "donation:" in str(d)

    def test_descr_contains_name(self):
        d = self._make(name="Bob Jones")
        assert "Bob Jones" in d.descr()


class TestCharge:
    def _make(self, **kwargs):
        defaults = dict(record=RECORD, filename="f.csv", service="stripe",
                        tx_id="CH1", date="2024-06-01", net="50.00",
                        name="Alice", description="Donation",
                        payment_service="stripe", payout_tx_id="PO1")
        defaults.update(kwargs)
        return Charge(**defaults)

    def test_payout_id(self):
        c = self._make(payment_service="stripe", payout_tx_id="PO1")
        assert c.payout_id == "stripe:PO1"

    def test_str_contains_charge(self):
        assert "charge:" in str(self._make())


class TestPayout:
    def test_str_contains_payout(self):
        p = Payout(RECORD, "f.csv", "stripe", "PO1", "2024-06-30", "500.00")
        assert "payout:" in str(p)

    def test_id(self):
        p = Payout(RECORD, "f.csv", "stripe", "PO1", "2024-06-30", "500.00")
        assert p.id == "stripe:PO1"


class TestReceipt:
    def _make(self, **kwargs):
        defaults = dict(record=RECORD, filename="f.csv", service="qbo",
                        tx_id="R1", date="2024-06-01", net="50.00",
                        name="Alice", ref_id="D1", product="Online Donation")
        defaults.update(kwargs)
        return Receipt(**defaults)

    def test_str_contains_receipt(self):
        assert "receipt:" in str(self._make())

    def test_no_donation_by_default(self):
        r = self._make()
        assert r.donation is None

    def test_no_discrepancies_by_default(self):
        r = self._make()
        assert r.discrepancies == []

    def test_descr_contains_id(self):
        r = self._make(tx_id="R99")
        assert "R99" in r.descr()
