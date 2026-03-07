#!/usr/bin/env python
"""Hash a password for use in users.json."""

import sys

import bcrypt


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <password>", file=sys.stderr)
        sys.exit(1)
    hashed = bcrypt.hashpw(sys.argv[1].encode(), bcrypt.gensalt())
    print(hashed.decode())


if __name__ == "__main__":
    main()
