import csv
import io
import pydoc
import re
from collections.abc import Generator, Iterator
from datetime import datetime
from typing import IO


def parse_datetime(dtstring: str, tmstring: str) -> tuple[datetime, datetime]:
    try:
        # Try parsing with a 4-digit year
        date = datetime.strptime(dtstring, '%m/%d/%Y')
    except ValueError:
        # Fallback to parsing with a 2-digit year
        date = datetime.strptime(dtstring, '%m/%d/%y')

    time = datetime.strptime(tmstring, '%H:%M:%S')
    return date, time

def shorten_gdrive_path(path: str) -> str:
    """ shorten Google Drive paths to just the file name """
    return re.sub(r'^.*EXPORTED REPORTS', '[gdrive EXPORTED]', path)

def csv_rows(csv_filename: str, skip: int = 0, take: int = -1) -> Generator[dict[str, str], None, None]:
    """ generator """
    with open(csv_filename, encoding='utf-8-sig') as csvin:
        for _ in range(skip):
            next(csvin)

        # Use DictReader for the remaining lines
        reader = csv.DictReader(csvin)
        taken = 0
        for row in reader:
            yield row

            taken += 1
            if 0 < take <= taken:
                break


def csv_rows_from_stream(csvin: IO[str]) -> Generator[dict[str, str], None, None]:
    """ generator """
    reader = csv.DictReader(csvin)
    for row in reader:
        yield row

def parse_float(number_str: str | float | int) -> float | None:
    """
    Parse a number string into a float while supporting formats with commas.
    Example: '2,000.22' -> 2000.22
    """
    if isinstance(number_str, (float, int)):   # in case already converted
        return float(number_str)

    try:
        # Remove commas, then parse as float
        return float(number_str.replace(',', ''))
    except ValueError as e:
        print(f"Error parsing number: {number_str} - {e}")
        return None

def paged_print(s: str, page_if: int = 30) -> None:
    string_buffer = io.StringIO(s)
    lines = string_buffer.readlines()
    line_count = len(lines)

    page_output = True
    if page_output and line_count > 30:
        pydoc.pager(s)
    else:
        print(s)


currency_symbols = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£"
}
def currency_symbol(curr_string: str) -> str:
    return currency_symbols.get(curr_string, curr_string)




"""
        process = sp.Popen(['less'], stdin=sp.PIPE, text=True)
        # Get the original stdout
        original_stdout = sys.stdout
        # Redirect stdout to the subprocess's stdin pipe
        sys.stdout = process.stdin
        sys.stdout = original_stdout

        # Close the stdin pipe and wait for the subprocess to finish
        process.stdin.close()
        process.wait()


"""
