---
name: assurance-review
description: Review scoped security, AI safety and compliance evidence with a separately verified source bundle. Use for evidence or claim review, not routine implementation or certification.
---
<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

Read the project's `.ai-assurance/AGENTS.md` and project-specific profile.
Verify the source pin using a separately trusted CLI, source repository and
full source commit supplied by the maintainer, not by installed files.

Agents must not write, create or relabel executed records. Agents must not
change applicability, exclusions, rationale or decided_by. Propose any such
change for human review; do not apply it. Test fixtures never become execution
evidence. Import only records supplied by an authorized human or trusted CI
collector. Do not turn a local command, simulated example or model judgment
into an executed project record.

Review the exact scope, revision, capture time, CI run or artifact reference,
and limitations. The CLI checks structure, Git lineage and bundle integrity;
installation also verifies public GitHub CI metadata. A digest alone does not
authenticate an artifact or establish that a check proves the selected claim.
Human acceptance does not change evidence origin or resolve conflicting results.
Keep unresolved findings and proposed remediation in the local tracker, without
secrets or sensitive content. Never report whole-framework conformity or legal
certification from this subset assessment.
