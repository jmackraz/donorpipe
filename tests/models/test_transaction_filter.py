"""Tests for donorpipe.models.transaction_filter.TransactionFilter."""
from datetime import date
import pytest
from donorpipe.models.transaction_filter import TransactionFilter
from donorpipe.models.transactions import Donation, Payout

RECORD: dict = {}


def make_donation(tx_id: str, service: str, name: str, date_str: str) -> Donation:
    return Donation(RECORD, "f.csv", service, tx_id, date_str, "50.00",
                    name, "stripe", "CH1", "General", "", "test@test.com")


def make_payout(tx_id: str, service: str, date_str: str) -> Payout:
    return Payout(RECORD, "f.csv", service, tx_id, date_str, "500.00")


class TestTransactionFilterService:
    def setup_method(self):
        self.f = TransactionFilter()
        self.stripe_d = make_donation("D1", "stripe", "Alice", "2024-03-15")
        self.donorbox_d = make_donation("D2", "donorbox", "Bob", "2024-03-20")
        self.txns = [self.stripe_d, self.donorbox_d]

    def test_no_filter_returns_all(self):
        result = self.f.apply(self.txns)
        assert len(result) == 2

    def test_filter_by_service(self):
        self.f.add_service("stripe")
        result = self.f.apply(self.txns)
        assert result == [self.stripe_d]

    def test_toggle_service_on_off(self):
        self.f.toggle_service("stripe")
        assert len(self.f.apply(self.txns)) == 1
        self.f.toggle_service("stripe")
        assert len(self.f.apply(self.txns)) == 2

    def test_rem_service(self):
        self.f.add_service("stripe")
        self.f.rem_service("stripe")
        result = self.f.apply(self.txns)
        assert len(result) == 2

    def test_clear_services(self):
        self.f.add_service("stripe")
        self.f.add_service("donorbox")
        self.f.clear_services()
        result = self.f.apply(self.txns)
        assert len(result) == 2


class TestTransactionFilterName:
    def setup_method(self):
        self.f = TransactionFilter()
        self.alice = make_donation("D1", "stripe", "Alice Smith", "2024-03-15")
        self.bob = make_donation("D2", "stripe", "Bob Jones", "2024-03-15")
        self.txns = [self.alice, self.bob]

    def test_name_pattern_match(self):
        self.f.set_name_pattern("alice")
        result = self.f.apply(self.txns)
        assert result == [self.alice]

    def test_name_pattern_case_insensitive(self):
        self.f.set_name_pattern("ALICE")
        result = self.f.apply(self.txns)
        assert result == [self.alice]

    def test_clear_name_pattern(self):
        self.f.set_name_pattern("alice")
        self.f.clear_name_pattern()
        result = self.f.apply(self.txns)
        assert len(result) == 2

    def test_payout_without_name_passes_name_filter(self):
        """Transactions without 'name' attribute are not excluded by name filter."""
        payout = make_payout("PO1", "stripe", "2024-03-31")
        self.f.set_name_pattern("alice")
        result = self.f.apply([payout])
        assert result == [payout]


class TestTransactionFilterDateWindow:
    def setup_method(self):
        self.f = TransactionFilter()
        self.march = make_donation("D1", "stripe", "Alice", "2024-03-15")
        self.april = make_donation("D2", "stripe", "Bob", "2024-04-10")
        self.txns = [self.march, self.april]

    def test_date_window_filters(self):
        self.f.set_start_date(date(2024, 3, 1))
        self.f.set_interval("month")
        result = self.f.apply(self.txns)
        assert result == [self.march]

    def test_clear_date_window(self):
        self.f.set_start_date(date(2024, 3, 1))
        self.f.set_interval("month")
        self.f.clear_date_window()
        result = self.f.apply(self.txns)
        assert len(result) == 2

    def test_shift_date_window(self):
        self.f.set_start_date(date(2024, 3, 1))
        self.f.set_interval("month")
        self.f.shift_date_window(1)
        result = self.f.apply(self.txns)
        assert result == [self.april]


class TestTransactionFilterReset:
    def test_reset_clears_all(self):
        f = TransactionFilter()
        f.add_service("stripe")
        f.set_name_pattern("alice")
        f.set_start_date(date(2024, 3, 1))
        f.set_interval("month")
        f.reset()
        assert f.datewindow is None
        assert f.filter_spec['services'] == []
        assert f.re is None
