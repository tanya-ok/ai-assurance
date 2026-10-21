# SPDX-FileCopyrightText: 2026 Tanya Babitskaya
# SPDX-License-Identifier: Apache-2.0
"""Exercise the public documentation artifact boundary with disposable fixtures."""

from __future__ import annotations

import importlib.util
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "check_docs", Path(__file__).resolve().parents[1] / "scripts/check_docs.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Documentation checker unavailable")
docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(docs)


class DocumentationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.site = Path(temporary.name) / "site"
        self.site.mkdir()
        (self.site / "index.html").write_text("<h1>Public documentation</h1>", encoding="utf-8")

    def test_public_site_passes_and_missing_build_is_refused(self) -> None:
        docs.check(self.site)
        with self.assertRaises(ValueError):
            docs.check(self.site / "absent")

    def test_private_paths_and_nested_content_are_refused(self) -> None:
        for relative in (".data/proof.json", "nested/AGENTS.local.md", "nested/output.log"):
            with self.subTest(relative=relative):
                path = self.site / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture", encoding="utf-8")
                try:
                    with self.assertRaises(ValueError):
                        docs.check(self.site)
                finally:
                    path.unlink()
                    if path.parent.name == ".data":
                        path.parent.rmdir()
        path = self.site / "nested/page.html"
        for value in ("op" + "://example.org/fixture", "/" + "Users/fixture/private/"):
            path.write_text(value, encoding="utf-8")
            with self.assertRaises(ValueError):
                docs.check(self.site)

    @unittest.skipUnless(os.name == "posix", "Link fixtures require POSIX")
    def test_symbolic_and_hard_links_are_refused(self) -> None:
        index = self.site / "index.html"
        link = self.site / "linked.html"
        link.symlink_to(index)
        with self.assertRaises(ValueError):
            docs.check(self.site)
        link.unlink()
        os.link(index, link)
        with self.assertRaises(ValueError):
            docs.check(self.site)
        link.unlink()
        alias = self.site.parent / "alias"
        alias.symlink_to(self.site, target_is_directory=True)
        with self.assertRaises(ValueError):
            docs.check(alias)

    def test_cli_failure_never_prints_matched_content(self) -> None:
        (self.site / "index.html").write_text(
            "op" + "://example.org/FIXTURE-SENSITIVE-OUTPUT", encoding="utf-8"
        )
        output = io.StringIO()
        with (
            patch.object(sys, "argv", ["check_docs", "--site", str(self.site)]),
            redirect_stdout(output),
        ):
            self.assertEqual(docs.main(), 1)
        self.assertEqual(output.getvalue(), "Documentation output requires private review\n")


if __name__ == "__main__":
    unittest.main()
