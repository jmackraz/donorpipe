"""Sanitize CSV files by replacing sensitive column values with synthetic stand-ins.

Usage:
    python scripts/sanitize_csv.py <input_dir> <output_dir>

Sensitive columns match: name, address, or comment (case-insensitive).
Each replaced cell becomes "{Label} {counter}" — counter is global across all files.
"""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

SENSITIVE_PATTERN = re.compile(r"name|donor|address|comment|email|company|description", re.IGNORECASE)


def _sensitive_label(header: str) -> str | None:
    """Return the capitalized label for a sensitive header, or None if not sensitive."""
    match = SENSITIVE_PATTERN.search(header)
    if match is None:
        return None
    return match.group(0).capitalize()


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
) -> None:
    """Read input_path, replace sensitive column values, write to output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    sensitive = {i: _sensitive_label(h) for i, h in enumerate(header)}
    half = len(header) / 2

    with output_path.open("w", newline="") as outfile:
        writer = csv.writer(outfile)
        # Write pre-header rows verbatim
        for row in rows[:header_idx]:
            writer.writerow(row)
        # Write header verbatim
        writer.writerow(header)
        # Write data and trailer rows
        for row in rows[header_idx + 1 :]:
            nonempty = sum(1 for cell in row if cell.strip())
            if nonempty < half:
                # Sparse row — trailer/summary, pass through verbatim
                writer.writerow(row)
            else:
                # Data row — sanitize sensitive columns
                new_row = list(row)
                for i, label in sensitive.items():
                    if label is not None and i < len(new_row):
                        counters[label] += 1
                        new_row[i] = f"{label} {counters[label]}"
                writer.writerow(new_row)


def sanitize_dir(input_dir: Path, output_dir: Path) -> None:
    """Recursively sanitize all CSV files in input_dir into output_dir."""
    print(f"Sanitizing {input_dir} to {output_dir}")
    counters: dict[str, int] = defaultdict(int)
    for input_path in sorted(input_dir.rglob("*.csv")):
        print(f"  {input_path}")
        relative = input_path.relative_to(input_dir)
        output_path = output_dir / relative
        sanitize_file(input_path, output_path, counters)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanitize sensitive columns in CSV files."
    )
    parser.add_argument("input_dir", type=Path, help="Directory of input CSV files")
    parser.add_argument("output_dir", type=Path, help="Directory for sanitized output")
    args = parser.parse_args()
    sanitize_dir(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
