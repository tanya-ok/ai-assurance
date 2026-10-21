# SPDX-FileCopyrightText: 2026 Tanya Babitskaya
# SPDX-License-Identifier: Apache-2.0
"""Refuse private paths and content before uploading the documentation site."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PRIVATE_PARTS = {".git", ".data", ".private", ".beads", ".dolt", ".ai-assurance", "private-review"}
PRIVATE_SUFFIXES = {".log", ".db", ".sqlite", ".pat", ".key", ".pem", ".patch", ".bundle"}
TEXT_SUFFIXES = {".html", ".md", ".txt", ".json", ".jsonl", ".svg", ".css", ".js", ".xml"}
PRIVATE_CONTENT = re.compile(
    rb"/(?:Users|home)/[^/\s]+/|\bop://[^\s]+|PRIVATE-REVIEW-ONLY|"
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"
)


def check(site: Path) -> None:
    if site.is_symlink() or not site.is_dir() or not (site / "index.html").is_file():
        raise ValueError("A built documentation site is required")
    for path in site.rglob("*"):
        relative = path.relative_to(site)
        if (
            path.is_symlink()
            or set(relative.parts) & PRIVATE_PARTS
            or path.name in {"AGENTS.local.md", "denylist.txt"}
            or path.suffix in PRIVATE_SUFFIXES
        ):
            raise ValueError("Private path in documentation output")
        if path.is_file():
            if path.stat().st_nlink != 1:
                raise ValueError("Linked files in documentation output are refused")
            if path.suffix in TEXT_SUFFIXES and PRIVATE_CONTENT.search(path.read_bytes()):
                raise ValueError("Private content in documentation output")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    args = parser.parse_args()
    try:
        check(args.site)
    except (OSError, ValueError):
        print("Documentation output requires private review")
        return 1
    print("Documentation output boundary passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
