"""Tests for donorpipe.datewindow.DateWindow."""
from datetime import date
import pytest
from donorpipe.datewindow import DateWindow, to_date
from datetime import datetime


class TestDateWindow:
    def test_month_interval_rounds_to_first(self):
        dw = DateWindow(start_date=date(2024, 3, 15), interval="month")
        assert dw.start_date == date(2024, 3, 1)

    def test_month_end_date(self):
        dw = DateWindow(start_date=date(2024, 3, 1), interval="month")
        assert dw.end_date == date(2024, 3, 31)

    def test_year_interval_rounds_to_jan_1(self):
        dw = DateWindow(start_date=date(2024, 6, 15), interval="year")
        assert dw.start_date == date(2024, 1, 1)
        assert dw.end_date == date(2024, 12, 31)

    def test_week_interval_rounds_to_monday(self):
        dw = DateWindow(start_date=date(2024, 3, 13), interval="week")  # Wednesday
        assert dw.start_date == date(2024, 3, 11)  # Monday

    def test_contains_within(self):
        dw = DateWindow(start_date=date(2024, 3, 1), interval="month")
        assert dw.contains(date(2024, 3, 15))

    def test_contains_boundary(self):
        dw = DateWindow(start_date=date(2024, 3, 1), interval="month")
        assert dw.contains(date(2024, 3, 1))
        assert dw.contains(date(2024, 3, 31))

    def test_not_contains_outside(self):
        dw = DateWindow(start_date=date(2024, 3, 1), interval="month")
        assert not dw.contains(date(2024, 2, 28))
        assert not dw.contains(date(2024, 4, 1))

    def test_shift_forward_month(self):
        dw = DateWindow(start_date=date(2024, 3, 1), interval="month")
        dw.shift_forward(1)
        assert dw.start_date == date(2024, 4, 1)
        assert dw.end_date == date(2024, 4, 30)

    def test_shift_backward_month(self):
        dw = DateWindow(start_date=date(2024, 3, 1), interval="month")
        dw.shift_backward(1)
        assert dw.start_date == date(2024, 2, 1)

    def test_str(self):
        dw = DateWindow(start_date=date(2024, 3, 1), interval="month")
        s = str(dw)
        assert "2024-03-01" in s
        assert "month" in s

    def test_invalid_interval_raises(self):
        with pytest.raises(ValueError):
            DateWindow(start_date=date(2024, 3, 1), interval="decade")

    def test_day_interval(self):
        dw = DateWindow(start_date=date(2024, 3, 15), interval="day")
        assert dw.start_date == date(2024, 3, 15)
        assert dw.end_date == date(2024, 3, 15)


class TestToDate:
    def test_date_passthrough(self):
        d = date(2024, 1, 1)
        assert to_date(d) == d

    def test_datetime_to_date(self):
        dt = datetime(2024, 6, 15, 10, 30)
        assert to_date(dt) == date(2024, 6, 15)

    def test_invalid_raises(self):
        with pytest.raises(TypeError):
            to_date("2024-01-01")  # type: ignore[arg-type]
