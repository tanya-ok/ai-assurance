<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Security policy

This is an experimental evidence-review tool, not an authorization service or
certification system. Version 0.2 is the only supported local development line.
Do not publish credentials, sensitive evidence or exploit details in public issues.
Contact the maintainer through the repository's private vulnerability-reporting
channel if one is available; otherwise request a private channel without details.
No public reporting channel is configured by this local prototype.

## Trust boundaries

- The separately installed CLI and maintainer-selected source repository/commit
  are trusted. Never execute installed managed code to establish its own trust.
- The lock, profile, evidence and project instructions are untrusted inputs.
  Bundle bytes are compared to the selected immutable Git objects. Git object
  integrity is not a signature or proof of repository ownership.
- An executed record must link to a commit that exists in the assessed repository
  and to a CI run or artifact digest. These checks do not authenticate artifact
  contents or prove that a test establishes the human-selected claim.
- Installation verifies public GitHub run/job metadata over HTTPS and refuses
  unavailable, mismatched or incomplete results. Private CI needs a future,
  explicitly reviewed collector; this version never accepts a token in a profile.
- Normal check/report operations are offline and do not re-query CI. They report
  linked evidence, not independently authenticated execution or current behavior.
- Applicability and decided_by remain human-supplied policy decisions. Agents must
  not alter them or create executed evidence. This is an instruction boundary,
  not cryptographic actor authentication.
- Installation is explicit, preserves other instructions and rolls back owned
  outputs on failure. Symlinks are refused. Do not concurrently edit the same
  project during installation; filesystem operations are not a sandbox.

No model API, clinical data system or cloud deployment is exercised by the local
control experiment. Organizational HIPAA requirements remain outside its proof.
