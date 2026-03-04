"""Tests for donorpipe.models.util."""
import io
import pytest
from donorpipe.models.util import parse_float, currency_symbol, shorten_gdrive_path, csv_rows_from_stream


class TestParseFloat:
    def test_plain_float_string(self):
        assert parse_float("1.23") == pytest.approx(1.23)

    def test_comma_formatted(self):
        assert parse_float("2,000.22") == pytest.approx(2000.22)

    def test_already_float(self):
        assert parse_float(3.14) == pytest.approx(3.14)

    def test_already_int(self):
        assert parse_float(42) == pytest.approx(42.0)

    def test_negative(self):
        assert parse_float("-50.00") == pytest.approx(-50.0)

    def test_invalid_returns_none(self, capsys):
        result = parse_float("not-a-number")
        assert result is None
        captured = capsys.readouterr()
        assert "Error parsing number" in captured.out


class TestCurrencySymbol:
    def test_usd(self):
        assert currency_symbol("USD") == "$"

    def test_eur(self):
        assert currency_symbol("EUR") == "€"

    def test_gbp(self):
        assert currency_symbol("GBP") == "£"

    def test_unknown_returns_code(self):
        assert currency_symbol("CAD") == "CAD"


class TestShortenGdrivePath:
    def test_shortens_gdrive_path(self):
        path = "/Users/alice/Google Drive/EXPORTED REPORTS/2024/file.csv"
        result = shorten_gdrive_path(path)
        assert result == "[gdrive EXPORTED]/2024/file.csv"

    def test_non_gdrive_path_unchanged(self):
        path = "/local/path/file.csv"
        assert shorten_gdrive_path(path) == path


class TestCsvRowsFromStream:
    def test_yields_dicts(self):
        data = "name,amount\nAlice,100\nBob,200\n"
        rows = list(csv_rows_from_stream(io.StringIO(data)))
        assert len(rows) == 2
        assert rows[0] == {"name": "Alice", "amount": "100"}
        assert rows[1] == {"name": "Bob", "amount": "200"}

    def test_empty_data(self):
        data = "name,amount\n"
        rows = list(csv_rows_from_stream(io.StringIO(data)))
        assert rows == []
