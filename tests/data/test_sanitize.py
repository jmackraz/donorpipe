"""Tests for scripts/sanitize_csv.py."""

import csv
import importlib.util
import re
from collections import defaultdict
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "sanitize_csv.py"


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


def test_sensitive_columns_replaced(tmp_path, mod):
    src = tmp_path / "in" / "a.csv"
    write_csv(
        src,
        [{"donor_name": "Alice", "amount": "100", "mailing_address": "123 Main St"}],
        ["donor_name", "amount", "mailing_address"],
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int))
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
    mod.sanitize_file(src, out, defaultdict(int))
    row = read_csv(out)[0]
    assert row["amount"] == "250"
    assert row["date"] == "2024-01-01"


def test_replacement_format(tmp_path, mod):
    src = tmp_path / "in" / "a.csv"
    write_csv(
        src,
        [
            {
                "donor_name": "Alice",
                "mailing_address": "123 Main",
                "internal_comment": "vip",
            }
        ],
        ["donor_name", "mailing_address", "internal_comment"],
    )
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int))
    row = read_csv(out)[0]
    pattern = re.compile(r"^(Name|Address|Comment) \d+$")
    assert pattern.match(row["donor_name"])
    assert pattern.match(row["mailing_address"])
    assert pattern.match(row["internal_comment"])


def test_headers_unchanged(tmp_path, mod):
    fieldnames = ["donor_name", "amount", "mailing_address"]
    src = tmp_path / "in" / "a.csv"
    write_csv(src, [{"donor_name": "Bob", "amount": "50", "mailing_address": "X"}], fieldnames)
    out = tmp_path / "out" / "a.csv"
    mod.sanitize_file(src, out, defaultdict(int))
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


def test_counters_are_global(tmp_path, mod):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    write_csv(
        in_dir / "a.csv",
        [{"donor_name": "Alice"}],
        ["donor_name"],
    )
    write_csv(
        in_dir / "b.csv",
        [{"donor_name": "Bob"}],
        ["donor_name"],
    )
    mod.sanitize_dir(in_dir, out_dir)
    row_a = read_csv(out_dir / "a.csv")[0]
    row_b = read_csv(out_dir / "b.csv")[0]
    assert row_a["donor_name"] != row_b["donor_name"]
    # Both should match the pattern
    pattern = re.compile(r"^Name \d+$")
    assert pattern.match(row_a["donor_name"])
    assert pattern.match(row_b["donor_name"])
    # Values across files are unique (global counter)
    vals = {row_a["donor_name"], row_b["donor_name"]}
    assert len(vals) == 2


def write_raw(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


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
    mod.sanitize_file(src, out, defaultdict(int))
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
    mod.sanitize_file(src, out, defaultdict(int))
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
    mod.sanitize_file(src, out, defaultdict(int))
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
    mod.sanitize_file(src, out, defaultdict(int))
    rows = read_csv(out)
    assert rows == []
