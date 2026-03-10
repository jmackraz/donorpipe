"""Tests for scripts/sanitize_csv.py."""

import csv
import importlib.util
import re
from collections import defaultdict
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "sanitize_csv.py"
TESTDATA_DIR = Path(__file__).parents[2] / "testdata"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("sanitize_csv", SCRIPT_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_raw(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# ---------------------------------------------------------------------------
# Fallback behavior (unknown file type → SENSITIVE_PATTERN + simple-sub)
# ---------------------------------------------------------------------------

def test_sensitive_columns_replaced(tmp_path, mod):
    src = tmp_path / "in" / "a.csv"
    write_csv(
        src,
        [{"donor_name": "Alice", "amount": "100", "mailing_address": "123 Main St"}],
        ["donor_name", "amount", "mailing_address"],
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    assert row["donor_name"] != "Alice"
    assert row["mailing_address"] != "123 Main St"


def test_nonsensitive_columns_preserved(tmp_path, mod):
    src = tmp_path / "in" / "a.csv"
    write_csv(
        src,
        [{"donor_name": "Alice", "amount": "250", "date": "2024-01-01"}],
        ["donor_name", "amount", "date"],
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    assert row["amount"] == "250"
    assert row["date"] == "2024-01-01"


def test_headers_unchanged(tmp_path, mod):
    fieldnames = ["donor_name", "amount", "mailing_address"]
    src = tmp_path / "in" / "a.csv"
    write_csv(src, [{"donor_name": "Bob", "amount": "50", "mailing_address": "X"}], fieldnames)
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    with out.open(newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == fieldnames


def test_recursive_structure(tmp_path, mod):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    sub = in_dir / "subdir"
    write_csv(
        sub / "b.csv",
        [{"donor_name": "Carol", "amount": "75"}],
        ["donor_name", "amount"],
    )
    mod.sanitize_dir(in_dir, out_dir)
    assert (out_dir / "subdir" / "b.csv").exists()


def test_address_still_uses_counter_format(tmp_path, mod):
    """Unknown file type falls back to simple-sub for address columns."""
    src = tmp_path / "in" / "a.csv"
    write_csv(
        src,
        [{"mailing_address": "123 Main St"}, {"mailing_address": "456 Elm Ave"}],
        ["mailing_address"],
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    rows = read_csv(out)
    assert re.match(r"^Address \d+$", rows[0]["mailing_address"])
    assert re.match(r"^Address \d+$", rows[1]["mailing_address"])


def test_preamble_rows_pass_through(tmp_path, mod):
    src = tmp_path / "in" / "a.csv"
    write_raw(
        src,
        "Report Title,,,\n"
        "Generated: 2024-01-01,,,\n"
        "donor_name,amount,date,mailing_address\n"
        "Alice,100,2024-01-01,123 Main St\n",
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    lines = out.read_text().splitlines()
    assert lines[0] == "Report Title,,,"
    assert lines[1] == "Generated: 2024-01-01,,,"
    assert lines[2] == "donor_name,amount,date,mailing_address"
    row = list(csv.DictReader([lines[2], lines[3]]))
    assert row[0]["donor_name"] != "Alice"
    assert row[0]["amount"] == "100"


def test_trailer_rows_pass_through(tmp_path, mod):
    src = tmp_path / "in" / "a.csv"
    write_raw(
        src,
        "donor_name,amount,date,mailing_address\n"
        "Alice,100,2024-01-01,123 Main St\n"
        "Total: 1 record,,,\n"
        "End of report,,,\n",
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    lines = out.read_text().splitlines()
    assert lines[0] == "donor_name,amount,date,mailing_address"
    assert lines[2] == "Total: 1 record,,,"
    assert lines[3] == "End of report,,,"
    row = list(csv.DictReader([lines[0], lines[1]]))
    assert row[0]["donor_name"] != "Alice"
    assert row[0]["amount"] == "100"


def test_preamble_and_trailer(tmp_path, mod):
    src = tmp_path / "in" / "a.csv"
    write_raw(
        src,
        "Report Title,,,\n"
        "donor_name,amount,date,mailing_address\n"
        "Alice,100,2024-01-01,123 Main St\n"
        "Total: 1 record,,,\n",
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    lines = out.read_text().splitlines()
    assert lines[0] == "Report Title,,,"
    assert lines[1] == "donor_name,amount,date,mailing_address"
    assert lines[3] == "Total: 1 record,,,"
    row = list(csv.DictReader([lines[1], lines[2]]))
    assert row[0]["donor_name"] != "Alice"
    assert row[0]["amount"] == "100"


def test_empty_rows_no_crash(tmp_path, mod):
    src = tmp_path / "in" / "empty.csv"
    src.parent.mkdir(parents=True, exist_ok=True)
    with src.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["donor_name", "amount"])
        writer.writeheader()
    out = tmp_path / "out" / "empty.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    rows = read_csv(out)
    assert rows == []


# ---------------------------------------------------------------------------
# Config-based behavior (donorbox file type)
# ---------------------------------------------------------------------------

def test_replacement_format(tmp_path, mod):
    """donorbox: Name → realistic name, Address → counter, Donor Comment → erased."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(
        src,
        [{"Name": "Alice Smith", "Address": "123 Main", "Donor Comment": "vip"}],
        ["Name", "Address", "Donor Comment"],
    )
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    assert row["Name"] in mod.REALISTIC_NAMES
    assert re.match(r"^Address \d+$", row["Address"])
    assert row["Donor Comment"] == ""


def test_same_name_maps_consistently(tmp_path, mod):
    """Same full name in two rows maps to the same fake name."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(
        src,
        [{"Name": "Alice Smith"}, {"Name": "Alice Smith"}],
        ["Name"],
    )
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    rows = read_csv(out)
    assert rows[0]["Name"] == rows[1]["Name"]
    assert rows[0]["Name"] in mod.REALISTIC_NAMES


def test_different_names_map_to_different_fakes(tmp_path, mod):
    """Different full names map to different fake names."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(
        src,
        [{"Name": "Alice Smith"}, {"Name": "Bob Jones"}],
        ["Name"],
    )
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    rows = read_csv(out)
    assert rows[0]["Name"] != rows[1]["Name"]


def test_names_are_global_and_consistent(tmp_path, mod):
    """Name mapping is shared across files in a sanitize_dir run."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    write_csv(in_dir / "donorbox_a.csv", [{"Name": "Alice Smith"}], ["Name"])
    write_csv(
        in_dir / "donorbox_b.csv",
        [{"Name": "Bob Jones"}, {"Name": "Alice Smith"}],
        ["Name"],
    )
    mod.sanitize_dir(in_dir, out_dir)
    row_a = read_csv(out_dir / "donorbox_a.csv")[0]
    rows_b = read_csv(out_dir / "donorbox_b.csv")
    assert row_a["Name"] in mod.REALISTIC_NAMES
    assert rows_b[0]["Name"] in mod.REALISTIC_NAMES
    # Alice in file a and Alice in file b map to the same fake name
    assert row_a["Name"] == rows_b[1]["Name"]
    # Alice and Bob get different fake names
    assert row_a["Name"] != rows_b[0]["Name"]


def test_first_last_name_coordinated(tmp_path, mod):
    """First and last name cols are derived from the same fake full name."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(
        src,
        [{"Donor's First Name": "Alice", "Donor's Last Name": "Smith"}],
        ["Donor's First Name", "Donor's Last Name"],
    )
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    fake_first = row["Donor's First Name"]
    fake_last = row["Donor's Last Name"]
    assert fake_first != "Alice"
    assert fake_last != "Smith"
    # Together they should form a name in REALISTIC_NAMES
    assert f"{fake_first} {fake_last}" in mod.REALISTIC_NAMES


def test_full_first_last_all_consistent(tmp_path, mod):
    """Full, first, and last name cols all derive from the same fake full name."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(
        src,
        [{"Name": "Alice Smith", "Donor's First Name": "Alice", "Donor's Last Name": "Smith"}],
        ["Name", "Donor's First Name", "Donor's Last Name"],
    )
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    fake_full = row["Name"]
    fake_first = row["Donor's First Name"]
    fake_last = row["Donor's Last Name"]
    assert fake_full in mod.REALISTIC_NAMES
    assert fake_full == f"{fake_first} {fake_last}"


def test_erase_classification(tmp_path, mod):
    """Columns classified 'erase' become empty strings."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(src, [{"Donor Comment": "vip donor"}], ["Donor Comment"])
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    assert row["Donor Comment"] == ""


def test_placeholder_classification(tmp_path, mod):
    """Columns classified 'placeholder' become the string 'placeholder'."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(src, [{"Donor Email": "alice@example.com"}], ["Donor Email"])
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    assert row["Donor Email"] == "placeholder"


def test_leave_classification(tmp_path, mod):
    """Columns classified 'leave' pass through unchanged."""
    src = tmp_path / "in" / "donorbox_test.csv"
    write_csv(src, [{"Donor Id": "12345"}], ["Donor Id"])
    out = tmp_path / "out" / "donorbox_test.csv"
    mod.sanitize_file(src, out, defaultdict(int), {})
    row = read_csv(out)[0]
    assert row["Donor Id"] == "12345"


# ---------------------------------------------------------------------------
# _get_file_type
# ---------------------------------------------------------------------------

def test_get_file_type(mod):
    assert mod._get_file_type("donorbox_2023.csv") == "donorbox"
    assert mod._get_file_type("stripe_2024.csv") == "stripe"
    assert mod._get_file_type("QBO_from_2023.csv") == "qbo"
    assert mod._get_file_type("Benevity August 2023 Download.csv") == "benevity"
    assert mod._get_file_type("chase_2025.csv") == "chase"
    assert mod._get_file_type("paypal_all_22Jul2023.csv") == "paypal"


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------

def test_validate_config_clean(mod):
    """validate_config reports no issues against the real testdata directory."""
    if not TESTDATA_DIR.exists():
        pytest.skip("testdata directory not present")
    issues = mod.validate_config(TESTDATA_DIR)
    assert issues == [], "\n".join(issues)


def test_validate_config_detects_missing(tmp_path, mod):
    """validate_config reports columns that are sensitive but not in config."""
    write_csv(
        tmp_path / "donorbox_test.csv",
        [{"Name": "Alice", "secret_name_field": "hidden"}],
        ["Name", "secret_name_field"],
    )
    issues = mod.validate_config(tmp_path)
    assert any("secret_name_field" in issue for issue in issues)


def test_validate_config_detects_unknown_type(tmp_path, mod):
    """validate_config reports files whose type is not in COLUMN_CONFIG."""
    write_csv(
        tmp_path / "unknown_source.csv",
        [{"donor_name": "Alice"}],
        ["donor_name"],
    )
    issues = mod.validate_config(tmp_path)
    assert any("unknown" in issue for issue in issues)
