from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

VALID_INTERVALS = {"day", "week", "month", "year"}


class DateWindow:
    def __init__(self, start_date: date = datetime.today(), interval: str = "month", count: int = 1):
        self.start_date = to_date(start_date)   # will be rounded in set_interval
        self.count = count
        self.interval = None
        self.set_interval(interval.lower(), count)  # will round start_date, set end

    def _validate_interval(self):
        if self.interval not in VALID_INTERVALS:
            raise ValueError(f"Invalid interval: {self.interval}. Must be one of {VALID_INTERVALS}.")

    def _round_to_interval_start(self, dt: date) -> date:
        if self.interval == "day":
            return dt
        elif self.interval == "week":
            start_of_week = dt - timedelta(days=dt.weekday())
            return start_of_week
        elif self.interval == "month":
            return dt.replace(day=1)
        elif self.interval == "year":
            return dt.replace(month=1, day=1)
        return dt

    def _update_end_date(self):
        """sets the end date based on the current interval, end point is inclusive"""
        if self.interval == "day":
            self.end_date = self.start_date + timedelta(days=self.count)
        elif self.interval == "week":
            self.end_date = self.start_date + timedelta(weeks=self.count)
        elif self.interval == "month":
            self.end_date = self.start_date + relativedelta(months=self.count)
        elif self.interval == "year":
            self.end_date = self.start_date + relativedelta(years=self.count)

        self.end_date = to_date(self.end_date) - timedelta(days=1)

    def set_start_date(self, new_start: date):
        """rounds the specified start date down to the first day of the calendar interval"""
        self._validate_interval()
        self.start_date = to_date(self._round_to_interval_start(new_start))
        self._update_end_date()

    def set_interval(self, interval: str, count: int = 1):
        self.interval = interval.lower()
        self.count = count
        self.set_start_date(self.start_date)  # Recalculate based on a new interval

    def contains(self, dt: date) -> bool:
        return self.start_date <= dt <= self.end_date

    def shift_forward(self, n: int = 1):
        if self.interval == "day":
            self.start_date += timedelta(days=self.count * n)
        elif self.interval == "week":
            self.start_date += timedelta(weeks=self.count * n)
        elif self.interval == "month":
            self.start_date += relativedelta(months=self.count * n)
        elif self.interval == "year":
            self.start_date += relativedelta(years=self.count * n)
        self._update_end_date()

    def shift_backward(self, n: int = 1):
        self.shift_forward(-n)

    def __str__(self):
        return f"Date from {self.start_date} to {self.end_date} ({self.interval} x {self.count})"

# utility
def to_date(d):
    if isinstance(d, datetime):
        return d.date()
    elif isinstance(d, date):
        return d
    else:
        raise TypeError("Expected a datetime or date object")
