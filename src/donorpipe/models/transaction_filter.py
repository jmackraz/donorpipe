import re
import copy
from datewindow import DateWindow

_initfilter_spec= {
    'services': [],
    'name': '.*',
}


class TransactionFilter:
    def __init__(self):
        self.datewindow = None
        self.filter_spec = copy.deepcopy(_initfilter_spec)
        self.re = None

    def reset(self):
        self.datewindow = None
        self.filter_spec = copy.deepcopy(_initfilter_spec)
        self.re = None

    def set_start_date(self, start_date):
        if self.datewindow:
            self.datewindow.set_start_date(start_date)
        else:
            self.datewindow = DateWindow(start_date=start_date)

    def set_interval(self, interval):
        if self.datewindow:
            self.datewindow.set_interval(interval)
        else:
            self.datewindow = DateWindow(interval=interval)

    def clear_date_window(self):
        self.datewindow = None

    def shift_date_window(self, count):
        if self.datewindow:
            self.datewindow.shift_forward(count)
        else:
            print("shift_date_window: no active date range")

    # SERVICE LIST MATCH

    def add_service(self, service):
        if service not in self.filter_spec['services']:
            self.filter_spec['services'].append(service)

    def rem_service(self, service):
        if service in self.filter_spec['services']:
            self.filter_spec['services'].remove(service)

    def toggle_service(self, service):
        if service in self.filter_spec['services']:
            self.filter_spec['services'].remove(service)
        else:
            self.filter_spec['services'].append(service)

    def clear_services(self):
        self.filter_spec['services'] = []

    # NAME PATTERN MATCH

    def set_name_pattern(self, pattern = None):
        """set regexp for filtering by name, clear with None. """
        self.filter_spec['name'] = pattern or '.*'
        self.re = re.compile(pattern, re.IGNORECASE)

    def clear_name_pattern(self):
        self.filter_spec['name'] = '.*'
        self.re = None


    def show_filters(self):
        """show current filter spec"""
        print("")
        print(self.datewindow if self.datewindow else "All dates")
        print(self.filter_spec)

    def apply(self, transactions):
        """filter a list of transactions based on our state"""
        filtered_transactions = transactions

        if self.filter_spec['services']:
            filtered_transactions = list(
                filter(lambda t: t.service in self.filter_spec['services'], filtered_transactions))

        # filter by name
        if self.re:
            filtered_transactions = list(
                filter(lambda t: not hasattr(t, 'name') or self.re.search(t.name), filtered_transactions))

        # filter by date window
        if self.datewindow:
            filtered_transactions = list(
                filter(lambda t: self.datewindow.contains(t.date), filtered_transactions))

        #print(f"filter applied, includes {len(filtered_transactions)} transactions")
        return filtered_transactions

