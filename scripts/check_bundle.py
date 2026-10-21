# SPDX-FileCopyrightText: 2026 Tanya Babitskaya
# SPDX-License-Identifier: Apache-2.0
"""Refuse unsynchronized bundles and a bundle edit without a version bump."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(base: str | None = None) -> None:
    source = ROOT / "src/ai_assurance/cli.py"
    if source.read_bytes() != (ROOT / "bundle/assurance.py").read_bytes():
        raise ValueError("Bundle runtime differs from canonical CLI")
    descriptor = json.loads((ROOT / "source.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "bundle/controls.json").read_text(encoding="utf-8"))
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = str(descriptor["version"])
    if (
        catalog["version"] != version
        or f'VERSION = "{version}"' not in source.read_text(encoding="utf-8")
        or f'version = "{version}"' not in metadata
    ):
        raise ValueError("Runtime, source, catalogue and package versions differ")
    if base:
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", base, "--", "bundle/"], cwd=ROOT
        ).strip()
        if changed:
            previous = json.loads(
                subprocess.check_output(
                    ["git", "show", base + ":bundle/controls.json"], cwd=ROOT
                ).decode("utf-8")
            )
            if previous["version"] == version:
                raise ValueError("Bundle changed without a VERSION bump")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base")
    args = parser.parse_args()
    verify(args.base)
    print("Bundle synchronization and version policy passed")


if __name__ == "__main__":
    main()
