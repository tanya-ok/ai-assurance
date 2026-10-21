<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Adoption is pending review

The portfolio was squashed on 2026-10-13. The old v0.1 instruction-scaffold
commits belong to historical local branches; they are not evidence of installation
in current releases. Do not replay them or install identical empty profiles.

Only proposals will be prepared, separately for each current `origin/main`, on
`chore/ai-assurance`. No target receives a `.ai-assurance/` installation or a
managed AGENTS block in this stage.

| Project | Proposed evidence focus | Required boundary |
|---|---|---|
| mcp-svid-auth | Scope/audience/credential and audit regression checks | Exclude managed assurance files from the sdist |
| hipaa-fhir-mcp | Input, synthetic data and audit-output checks | No HIPAA certification or clinical-backend claim |
| engineering-os | Retrieval, routing and privacy regressions | Knowledge never grants write authority |
| it-grc | Evidence, review and unknown/gap distinctions | Human review does not change evidence origin |
| mcp-spiffe-bridge | Transport and credential regressions | Node-only target; a Python 3.12+ verification runner would need approval |

`ecs-contract` is excluded. Linear is optional; no tracker or model quorum is a
source of execution authority. Future installation needs explicit approval,
project-specific claims tied to named CI checks, and actual verifiable CI runs.
A proposed profile is not an accepted applicability decision or executed record.
