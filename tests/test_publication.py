# SPDX-FileCopyrightText: 2026 Tanya Babitskaya
# SPDX-License-Identifier: Apache-2.0
"""Publication boundaries and reproducible source packaging metadata."""

from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def test_apache_notice_and_source_spdx_identifiers(self) -> None:
        self.assertIn("Apache License", (ROOT / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn(
            "Copyright 2026 Tanya Babitskaya", (ROOT / "NOTICE").read_text(encoding="utf-8")
        )
        for directory in ("src", "tools", "scripts", "tests", "bundle"):
            for path in (ROOT / directory).rglob("*.py"):
                with self.subTest(path=path):
                    first = path.read_text(encoding="utf-8").splitlines()[:2]
                    self.assertIn("# SPDX-FileCopyrightText: 2026 Tanya Babitskaya", first)
                    self.assertIn("# SPDX-License-Identifier: Apache-2.0", first)
        self.assertIn(
            "SPDX-License-Identifier: Apache-2.0",
            (ROOT / "bundle/controls.json.license").read_text(encoding="utf-8"),
        )

    def test_publication_files_entrypoint_and_sdist_exclusions(self) -> None:
        for name in (
            "README.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CHANGELOG.md",
            "pyproject.toml",
        ):
            self.assertTrue((ROOT / name).is_file(), name)
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(metadata["project"]["scripts"]["ai-assurance"], "ai_assurance.cli:main")
        self.assertEqual(metadata["project"]["license"], "Apache-2.0")
        self.assertTrue(metadata["tool"]["mypy"]["strict"])
        self.assertIn(
            "/.ai-assurance", metadata["tool"]["hatch"]["build"]["targets"]["sdist"]["exclude"]
        )
        self.assertIn("/.beads", metadata["tool"]["hatch"]["build"]["targets"]["sdist"]["exclude"])

    def test_ci_uses_immutable_actions_and_required_gates(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        uses = re.findall(r"uses: ([^\s]+)", workflow)
        self.assertGreaterEqual(len(uses), 4)
        for action in uses:
            self.assertRegex(action, r"^[A-Za-z0-9_./-]+@[0-9a-f]{40}$")
        for gate in (
            "unittest discover",
            "ruff check",
            "ruff format --check",
            "mypy",
            "zensical build --strict --clean",
            "gitleaks/gitleaks-action@",
            "check_bundle.py",
        ):
            self.assertIn(gate, workflow)
        self.assertNotIn("write-all", workflow)

    def test_node_only_and_pending_adoption_are_explicit(self) -> None:
        for name in ("README.md", "docs/adoption.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("ecs-contract", text)
            self.assertIn("it-grc", text)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Python 3.12+ and Git", readme)
        self.assertIn("No portfolio installations are authorized", readme)


if __name__ == "__main__":
    unittest.main()
