# SPDX-FileCopyrightText: 2026 Tanya Babitskaya
# SPDX-License-Identifier: Apache-2.0
"""Source-checkout compatibility entry point; prefer the installed ai-assurance CLI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ai_assurance.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
