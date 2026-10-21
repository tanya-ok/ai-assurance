<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# AI Assurance

Security, AI safety and compliance evidence with explicit scope and source trust.

**A linked test result supports a bounded claim. It is not certification.**

Local prototype, Apache-2.0. No portfolio installations are authorized yet.
The old v0.1 scaffolds are not the current adoption plan. `ecs-contract` is excluded.
CISO Assistance is now `it-grc`.

## Check the project

```sh
uv sync --locked --all-groups
uv run python -m unittest discover -s tests -v
uv run ruff check .
uv run ruff format --check src tools scripts tests bundle
uv run mypy
uv run python scripts/check_bundle.py
uv run zensical build --strict --clean
```

## Source verification and explicit installation

Use a separately trusted CLI, a trusted source checkout, and a reviewed full
40-hex source commit. Never take the source pin from the target's lock file.
Python 3.12+ and Git are required, including when the target is Node-only.

Select the reviewed 0.2.1 source revision externally and verify its five payload
files against an immutable Git bundle. Dependent proposals name the exact source
commit; this repository does not embed its own changing commit ID. The selected
revision must be available before adoption. Source verification does not
authenticate the contents of a later evidence record.

```sh
ai-assurance check /path/to/project --source-repo /path/to/ai-assurance --source-commit REVIEWED_40_HEX_COMMIT
ai-assurance report /path/to/project --source-repo /path/to/ai-assurance --source-commit REVIEWED_40_HEX_COMMIT
```

Installation is a separate, explicit operation requiring `--profile` and
`--evidence` inputs. There is no generated default profile or empty scaffold.
It verifies actual public GitHub workflow/job metadata for selected CI evidence.
Unavailable or private CI is refused; no access token is accepted in a profile.
No installation into portfolio repositories is part of the current work.

`project_id` is a stable user-selected identifier, not a checkout directory name.
An executed record needs an existing full commit, a non-future timestamp and a
run URL or SHA-256 artifact reference. Applicability exclusions need rationale
and decided_by. Agents must not edit applicability or create executed records.

## Local control experiment

```sh
uv run python tools/control_experiment.py --json docs/assets/control-results.json --markdown docs/results.md
```

This executes fixed proposals against an in-memory synthetic store, comparing
unrestricted, deny-all and bounded controls. No LLM, real PHI or cloud is used.
It does not create project CI execution records or certify HIPAA compliance.

[Research](docs/research.md) | [Threat model](SECURITY.md) | [PoC](docs/poc.md) |
[Adoption proposals](docs/adoption.md) | [Contributing](CONTRIBUTING.md)

[Local verification and adoption boundaries](docs/validation.md)

## Documentation publishing

The Pages workflow builds and checks the static documentation. Upload and deploy
require `main`, the `github-pages` environment and the explicit repository variable
`PAGES_ENABLED=true`. Enable them only after reviewing the public output and
approving publication. Workflow preparation alone does not publish a site.
