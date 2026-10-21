<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Local verification

46 offline unit tests, Ruff lint and formatting, strict mypy, bundle synchronization,
strict Zensical documentation and wheel/source builds passed locally. Mocked CI
fixtures are not real project execution evidence. No remote CI, portfolio
installation, deployment or publication was performed.

## Source and evidence boundaries

AI Assurance 0.2.1 uses a separately trusted CLI and an externally reviewed full
source commit. Dependent proposals name that commit and require it to be
available before adoption. Verify the selected revision against an immutable Git
bundle; do not copy a historical source pin from an earlier development branch.
The runtime, catalogue and package versions agree with the reviewed source bundle.

Executed records require an existing full project commit, a non-future timestamp
and a run URL or artifact digest. The current installer also verifies public
GitHub workflow/job metadata. Source verification alone cannot authenticate an
evidence claim. Agents may not create executed records or decide applicability.

## Proposed portfolio profiles

The project-specific proposals for `mcp-svid-auth`, `hipaa-fhir-mcp`,
`engineering-os`, `it-grc` and `mcp-spiffe-bridge` remain review envelopes on
separate `chore/ai-assurance` branches. They are not installer inputs, approved
applicability decisions or execution records. No portfolio installation is
authorized. `ecs-contract` remains excluded.

MCP SVID's proposal excludes managed assurance state from source distributions.
Private CI is unsupported by the current public-only verifier; IT GRC needs a
separately reviewed evidence collector. Bridge installation remains out of
scope, and any future external verifier requires Python 3.12+ and Git. No Python
dependency was added to that Node-only project.
