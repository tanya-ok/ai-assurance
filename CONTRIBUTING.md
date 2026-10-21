<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Contributing

Use Python 3.12+, Git and uv. Keep changes on a feature branch; local work does
not authorize a push, release or installation into another repository.

```sh
uv sync --locked --all-groups
uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run ruff format --check src tools scripts tests bundle
uv run mypy
uv run python scripts/check_bundle.py --base YOUR_BASE_COMMIT
uv run zensical build --strict --clean
uv build
```

Run Gitleaks on both the working tree and Git history before publication.
Every change to `bundle/` needs a new VERSION in the canonical runtime,
`source.json`, catalogue and pyproject. Copy `src/ai_assurance/cli.py` to
`bundle/assurance.py`; the synchronization gate rejects drift and version reuse.

Add a regression test for every trust-boundary change. Test evidence is synthetic
and mocked; it never becomes real project execution evidence. Do not write
executed records or change project applicability as an agent. Propose the change
for a maintainer or trusted CI collector to handle separately.

Only a maintainer-selected full Git commit from a trusted source repository is a
source pin. A lock-selected commit is not a trust anchor. Publication includes no
portfolio installation; installation needs separate approval, a project-specific
profile and verifiable CI evidence.
