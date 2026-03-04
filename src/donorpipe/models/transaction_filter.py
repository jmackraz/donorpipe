from __future__ import annotations

import re
import copy
from typing import Any

from donorpipe.datewindow import DateWindow
from donorpipe.models.transactions import Transaction

_initfilter_spec: dict[str, Any] = {
    'services': [],
    'name': '.*',
}


class TransactionFilter:
    def __init__(self) -> None:
        self.datewindow: DateWindow | None = None
        self.filter_spec: dict[str, Any] = copy.deepcopy(_initfilter_spec)
        self.re: re.Pattern[str] | None = None

    def reset(self) -> None:
        self.datewindow = None
        self.filter_spec = copy.deepcopy(_initfilter_spec)
        self.re = None

    def set_start_date(self, start_date: Any) -> None:
        if self.datewindow:
            self.datewindow.set_start_date(start_date)
        else:
            self.datewindow = DateWindow(start_date=start_date)

    def set_interval(self, interval: str) -> None:
        if self.datewindow:
            self.datewindow.set_interval(interval)
        else:
            self.datewindow = DateWindow(interval=interval)

    def clear_date_window(self) -> None:
        self.datewindow = None

    def shift_date_window(self, count: int) -> None:
        if self.datewindow:
            self.datewindow.shift_forward(count)
        else:
            print("shift_date_window: no active date range")

    # SERVICE LIST MATCH

    def add_service(self, service: str) -> None:
        if service not in self.filter_spec['services']:
            self.filter_spec['services'].append(service)

    def rem_service(self, service: str) -> None:
        if service in self.filter_spec['services']:
            self.filter_spec['services'].remove(service)

    def toggle_service(self, service: str) -> None:
        if service in self.filter_spec['services']:
            self.filter_spec['services'].remove(service)
        else:
            self.filter_spec['services'].append(service)

    def clear_services(self) -> None:
        self.filter_spec['services'] = []

    # NAME PATTERN MATCH

    def set_name_pattern(self, pattern: str | None = None) -> None:
        """set regexp for filtering by name, clear with None. """
        self.filter_spec['name'] = pattern or '.*'
        self.re = re.compile(pattern, re.IGNORECASE)  # type: ignore[arg-type]

    def clear_name_pattern(self) -> None:
        self.filter_spec['name'] = '.*'
        self.re = None


    def show_filters(self) -> None:
        """show current filter spec"""
        print("")
        print(self.datewindow if self.datewindow else "All dates")
        print(self.filter_spec)

    def apply(self, transactions: list[Transaction]) -> list[Transaction]:
        """filter a list of transactions based on our state"""
        filtered_transactions = transactions

        if self.filter_spec['services']:
            filtered_transactions = list(
                filter(lambda t: t.service in self.filter_spec['services'], filtered_transactions))

        # filter by name
        if self.re:
            filtered_transactions = list(
                filter(lambda t: not hasattr(t, 'name') or self.re.search(t.name), filtered_transactions))  # type: ignore[union-attr]

        # filter by date window
        if self.datewindow:
            filtered_transactions = list(
                filter(lambda t: self.datewindow.contains(t.date), filtered_transactions))  # type: ignore[union-attr]

        #print(f"filter applied, includes {len(filtered_transactions)} transactions")
        return filtered_transactions
