"""Sanitize CSV files by replacing sensitive column values with synthetic stand-ins.

Usage:
    python scripts/sanitize_csv.py <input_dir> <output_dir>
    python scripts/sanitize_csv.py --validate <input_dir>

File type is determined by the first token of the filename (split on '_' or space),
lowercased. Each file type has a config dict mapping column names to a classification:

    full-name   Replace with a realistic fake full name (consistent per original value)
    first-name  Replace with the first token of the fake full name (row-coordinated)
    last-name   Replace with the remaining tokens of the fake full name (row-coordinated)
    simple-sub  Legacy counter: "Address 1", "Address 2", etc.
    placeholder Replace with the literal string "placeholder"
    erase       Replace with an empty string
    leave       Pass through unchanged (looks sensitive but isn't)

Columns not in the config for the file type fall back to the SENSITIVE_PATTERN +
simple-sub behavior (preserves compatibility for unknown file types).
"""

import argparse
import csv
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

# NBA All-Star players, roughly 2014–2024.
REALISTIC_NAMES: list[str] = [
    "LeBron James", "Kevin Durant", "Stephen Curry", "James Harden", "Anthony Davis",
    "Kawhi Leonard", "Giannis Antetokounmpo", "Damian Lillard", "Paul George", "Kyrie Irving",
    "Russell Westbrook", "Chris Paul", "Blake Griffin", "Klay Thompson", "Draymond Green",
    "Carmelo Anthony", "DeMar DeRozan", "John Wall", "Kyle Lowry", "Kemba Walker",
    "Bradley Beal", "Devin Booker", "Donovan Mitchell", "Luka Doncic", "Jayson Tatum",
    "Trae Young", "Nikola Jokic", "Joel Embiid", "Karl-Anthony Towns", "Rudy Gobert",
    "Domantas Sabonis", "Bam Adebayo", "Zach LaVine", "Andrew Wiggins", "Ja Morant",
    "De'Aaron Fox", "Fred VanVleet", "Tyrese Haliburton", "Evan Mobley", "Jaren Jackson Jr.",
    "Darius Garland", "Desmond Bane", "Tyler Herro", "Shai Gilgeous-Alexander", "Scottie Barnes",
    "Cade Cunningham", "Franz Wagner", "Victor Wembanyama", "Paolo Banchero", "Lauri Markkanen",
]

# Per-file-type column classification config.
# Keys are exact column header strings as they appear in the CSV.
# File type = first token of filename (split on '_' or space), lowercased.
COLUMN_CONFIG: dict[str, dict[str, str]] = {
    "donorbox": {
        "Name":                            "full-name",
        "Donating Company":                "simple-sub",
        "Donor's First Name":              "first-name",
        "Donor's Last Name":               "last-name",
        "Donor Email":                     "placeholder",
        "Donor Comment":                   "erase",
        "Address":                         "simple-sub",
        "Address 2":                       "simple-sub",
        "Donor Id":                        "leave",
        "Fair Market Value Description":   "leave",
        "Amount Description":              "leave",
        "Honoree Name":                    "full-name",
        "Recipient Name":                  "full-name",
        "Recipient Email":                 "placeholder",
        "Recipient Address":               "simple-sub",
    },
    "stripe": {
        "Description":                               "placeholder",
        "description (metadata)":                    "leave",
        "donorbox_name (metadata)":                  "full-name",
        "donorbox_first_name (metadata)":            "first-name",
        "donorbox_last_name (metadata)":             "last-name",
        "donorbox_email (metadata)":                 "placeholder",
        "donorbox_address (metadata)":               "simple-sub",
        "donorbox_address_line_2 (metadata)":        "simple-sub",
        "donorbox_postal_code (metadata)":           "simple-sub",
        "donorbox_country (metadata)":               "leave",
        "donorbox_state (metadata)":                 "leave",
        "donorbox_city (metadata)":                  "leave",
        "donorbox_donor_id (metadata)":              "leave",
        "donorbox_recurring_donation (metadata)":    "leave",
        "donorbox_first_recurring_charge (metadata)": "leave",
        "donorbox_designation (metadata)":           "leave",
        "donorbox_campaign (metadata)":              "leave",
        "donorbox_form_id (metadata)":               "leave",
        "donorbox_plan_interval (metadata)":         "leave",
        "donorbox_donation_type (metadata)":         "leave",
        "donorbox_gift_aid (metadata)":              "leave",
        "donorbox_idempotency_key (metadata)":       "leave",
    },
    "qbo": {
        "Donor":                           "full-name",
        "Product/Service full name":       "leave",
    },
    "paypal": {
        "Name":                                     "full-name",
        "From Email Address":                       "placeholder",
        "To Email Address":                         "placeholder",
        "Shipping Address":                         "simple-sub",
        "Address Line 1":                           "simple-sub",
        "Address Line 2/District/Neighborhood":     "simple-sub",
        "Option 1 Name":                            "leave",
        "Option 2 Name":                            "leave",
        "Address Status":                           "leave",
    },
    "chase": {
        "Description":                     "leave",
    },
    "benevity": {
        "Company":                         "simple-sub",
        "Donor First Name":                "first-name",
        "Donor Last Name":                 "last-name",
        "Email":                           "placeholder",
        "Address":                         "simple-sub",
        "Comment":                         "erase",
        "Fee Comment":                     "leave",
    },
}

SENSITIVE_PATTERN = re.compile(r"name|donor|address|comment|email|company|description", re.IGNORECASE)

_NAME_CLASSES = frozenset({"full-name", "first-name", "last-name"})


def _get_file_type(filename: str) -> str:
    """Return the file type key from a filename (first token, lowercased)."""
    return filename.replace("_", " ").split()[0].lower()


def _normalize_name(name: str) -> str:
    """Normalize a name for consistent hashing: lowercase, collapse whitespace."""
    return " ".join(name.lower().split())


def _assign_name(original: str, name_map: dict[str, str]) -> str:
    """Return a consistent realistic fake name for the given original value.

    The lookup key is normalized (lowercase, whitespace-collapsed) so that
    "Alice Smith", "ALICE SMITH", and "alice smith" all map to the same fake name.
    """
    key = _normalize_name(original)
    if key not in name_map:
        idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(REALISTIC_NAMES)
        name_map[key] = REALISTIC_NAMES[idx]
    return name_map[key]


def _sanitize_name_fields(
    row: list[str],
    name_indices: dict[int, str],
    name_map: dict[str, str],
) -> None:
    """Substitute full/first/last name fields consistently across a single row."""
    full_idx = next((i for i, c in name_indices.items() if c == "full-name"), None)
    first_idx = next((i for i, c in name_indices.items() if c == "first-name"), None)
    last_idx = next((i for i, c in name_indices.items() if c == "last-name"), None)

    # Determine hash key: prefer full-name cell, else concat first+last
    if full_idx is not None and row[full_idx].strip():
        key = row[full_idx].strip()
    else:
        parts = []
        if first_idx is not None and row[first_idx].strip():
            parts.append(row[first_idx].strip())
        if last_idx is not None and row[last_idx].strip():
            parts.append(row[last_idx].strip())
        key = " ".join(parts)

    if not key:
        return

    fake_full = _assign_name(key, name_map)
    fake_first, fake_last = fake_full.split(" ", 1) if " " in fake_full else (fake_full, "")

    if full_idx is not None:
        row[full_idx] = fake_full
    if first_idx is not None:
        row[first_idx] = fake_first
    if last_idx is not None:
        row[last_idx] = fake_last

    # Hash any additional full-name columns independently (e.g. Honoree Name,
    # Recipient Name — different people, not coordinated with first/last).
    for i, cls in name_indices.items():
        if cls == "full-name" and i != full_idx and row[i].strip():
            row[i] = _assign_name(row[i], name_map)


def _sensitive_label(header: str) -> str:
    """Return a capitalized label for use in simple-sub counters."""
    match = SENSITIVE_PATTERN.search(header)
    return match.group(0).capitalize() if match else "Field"


def find_header_row(rows: list[list[str]]) -> int:
    """Return the index of the first row with the maximum number of non-empty fields."""
    if not rows:
        return 0
    counts = [sum(1 for cell in row if cell.strip()) for row in rows]
    max_count = max(counts)
    return next(i for i, c in enumerate(counts) if c == max_count)


def sanitize_file(
    input_path: Path,
    output_path: Path,
    counters: dict[str, int],
    name_map: dict[str, str],
) -> None:
    """Read input_path, replace sensitive column values, write to output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("sanitize file:", input_path)

    with input_path.open(newline="") as infile:
        rows = list(csv.reader(infile))

    if not rows:
        output_path.write_text(input_path.read_text())
        return

    header_idx = find_header_row(rows)
    header = rows[header_idx]

    if not any(cell.strip() for cell in header):
        output_path.write_text(input_path.read_text())
        return

    file_type = _get_file_type(input_path.name)

    print("file type:", file_type)

    col_config = COLUMN_CONFIG.get(file_type)
    # Known file types (e.g. DonorBox API downloads) may have many intentionally
    # empty columns, so use a lower sparsity threshold to avoid skipping real rows.
    half = len(header) / 4 if col_config is not None else len(header) / 2

    if not col_config:
        print("column config is None")

    with output_path.open("w", newline="") as outfile:
        writer = csv.writer(outfile)
        for row in rows[:header_idx]:
            writer.writerow(row)
        writer.writerow(header)
        for row in rows[header_idx + 1 :]:
            nonempty = sum(1 for cell in row if cell.strip())
            if nonempty < half:
                writer.writerow(row)
                continue

            new_row = list(row)

            if col_config is None:
                # Unknown file type: fall back to SENSITIVE_PATTERN + simple-sub
                print("unknown file type, falling back to SENSITIVE_PATTERN + simple-sub")
                for i, h in enumerate(header):
                    if i < len(new_row) and SENSITIVE_PATTERN.search(h):
                        label = _sensitive_label(h)
                        counters[label] += 1
                        new_row[i] = f"{label} {counters[label]}"
            else:
                # Coordinated name substitution first
                name_indices = {
                    i: col_config[h]
                    for i, h in enumerate(header)
                    if i < len(new_row) and col_config.get(h) in _NAME_CLASSES
                }
                print("name indices:", len(name_indices), name_indices)
                if name_indices:
                    _sanitize_name_fields(new_row, name_indices, name_map)

                # Remaining classified columns
                for i, h in enumerate(header):
                    if i >= len(new_row):
                        continue
                    cls = col_config.get(h)
                    if cls is None or cls in _NAME_CLASSES or cls == "leave":
                        continue
                    elif cls == "erase":
                        new_row[i] = ""
                    elif cls == "placeholder":
                        new_row[i] = "placeholder"
                    elif cls == "simple-sub":
                        label = _sensitive_label(h)
                        counters[label] += 1
                        new_row[i] = f"{label} {counters[label]}"

            writer.writerow(new_row)


def validate_config(data_dir: Path) -> list[str]:
    """Check that all sensitive columns in data_dir CSVs are covered by COLUMN_CONFIG.

    Returns a list of issue strings; empty means everything is accounted for.
    """
    issues: list[str] = []
    for csv_path in sorted(data_dir.rglob("*.csv")):
        file_type = _get_file_type(csv_path.name)
        col_config = COLUMN_CONFIG.get(file_type)
        if col_config is None:
            issues.append(f"Unknown file type '{file_type}': {csv_path.name}")
            continue
        with csv_path.open(newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        header = rows[find_header_row(rows)]
        for col in header:
            if SENSITIVE_PATTERN.search(col) and col not in col_config:
                issues.append(f"{file_type}: column '{col}' not in config ({csv_path.name})")
    return issues


def sanitize_dir(input_dir: Path, output_dir: Path) -> None:
    """Recursively sanitize all CSV files in input_dir into output_dir."""
    print(f"Sanitizing {input_dir} to {output_dir}")
    counters: dict[str, int] = defaultdict(int)
    name_map: dict[str, str] = {}
    for input_path in sorted(input_dir.rglob("*.csv")):
        print(f"  {input_path}")
        relative = input_path.relative_to(input_dir)
        output_path = output_dir / relative
        sanitize_file(input_path, output_path, counters, name_map)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanitize sensitive columns in CSV files."
    )
    parser.add_argument("input_dir", type=Path, help="Directory of input CSV files")
    parser.add_argument(
        "output_dir", type=Path, nargs="?",
        help="Directory for sanitized output (omit when using --validate)"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Check that all sensitive columns are covered by COLUMN_CONFIG and exit"
    )
    args = parser.parse_args()

    if args.validate:
        issues = validate_config(args.input_dir)
        if issues:
            for issue in issues:
                print(issue)
            sys.exit(1)
        else:
            print("Config OK — all sensitive columns accounted for.")
    else:
        if args.output_dir is None:
            parser.error("output_dir is required when not using --validate")
        sanitize_dir(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
