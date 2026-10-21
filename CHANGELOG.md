<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

## 0.2.1

- Improve local verification and documentation delivery.

## 0.2.0

- Add Apache-2.0 licensing, SPDX identifiers, packaging and local CI definitions.
- Verify bundle bytes and source identity against a separately selected Git commit;
  reject bundle-version reuse and uncommitted source-tree substitution.
- Require real commit lineage, non-future capture time and run/artifact references.
- Require project-specific claims, named CI checks, actual verified CI for install,
  and an attributed human decision for not-applicable requirements.
- Support renamed checkouts, worktrees and forks through a stable project_id.
- Add bounded instruction markers, rollback and explicit UTF-8 handling.
- Withdraw the old empty portfolio scaffolds from the current adoption plan.
  No current portfolio release is installed by this work.

## 0.1.0 - 2026-10-13

Initial local experiment and maintenance-scaffold prototype. Its old local
integration commits are not part of the squashed portfolio release. Its manifest
alone did not establish a source pin; do not use that version for installation.
