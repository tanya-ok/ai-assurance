<!-- SPDX-FileCopyrightText: 2026 Tanya Babitskaya -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Project Sprint brief

## Testable agent controls with useful work preserved

A focused research-engineering project within AI Assurance.

**Research question:** under a fixed synthetic workflow and explicit threat
model, which application controls prevent unauthorized agent actions while
preserving authorized task completion?

**Hypothesis:** an action broker using host-owned resource/tool grants and exact
write authorization will satisfy more adversarial outcome checks than an
unrestricted baseline, while completing more legitimate tasks than deny-all.
The initial PoC tests this on fixed proposals. Real-model behavior remains a
separate experiment.

## Fit to the public course

The [Technical AI Safety Project curriculum](https://bluedot.org/courses/technical-ai-safety-project/1/1)
organizes work around choosing a project, testing ideas, iteration, writing and a
demo. We adapt that sequence below. Account-only exercises and detailed
[evaluation criteria](https://bluedot.org/courses/technical-ai-safety-project/5/1)
were not visible in public research. These are our acceptance criteria, not a
claim to satisfy the course's private rubric.

| Public stage | Our artifact | Acceptance |
|---|---|---|
| [Scope it down](https://bluedot.org/courses/technical-ai-safety-project/1/4) | One workflow, one action boundary, fixed resources | No all-purpose alignment or compliance claim |
| [What needs to be true](https://bluedot.org/courses/technical-ai-safety-project/2/2) | Threat assumptions, hypothesis and failure oracle | Permissions cannot originate in the proposal |
| [What to test first](https://bluedot.org/courses/technical-ai-safety-project/2/3) | Baselines plus unauthorized read/write/export and replay | Actual outputs and store changes are inspected |
| [Use the results](https://bluedot.org/courses/technical-ai-safety-project/3/1) | Failure inventory and next experiment | Report unfavorable results as well as passes |
| Write and demonstrate | Replayable runner, JSON evidence and short report | Another engineer can reproduce the finite-suite outcome |

## Experiment contract

- **Independent variable:** unrestricted, deny-all or bounded permission broker.
- **Inputs:** independently authored proposals and host-owned synthetic session
  context. The local suite is development data, not a held-out benchmark.
- **Outcomes:** scenario expectations satisfied, legitimate tasks completed,
  protected fields disclosed and unauthorized state changes. No single safety
  score combines these different quantities.
- **Decision rule:** every local bounded scenario must match its stated outcome;
  failures require investigation. This is a finite test gate, not a population
  risk estimate.
- **Failure conditions:** proposal-supplied authority accepted, changed approval
  replayed, cancelled work executes, protected data returned, or deny-all mistaken
  for useful control.

## Sprint plan

1. Freeze the question, assumptions, scenarios and baselines with a reviewer.
2. Reproduce the local PoC and identify missing attack surfaces.
3. Add one real-model evaluation adapter using a selected framework such as
   Inspect AI. Use synthetic data, frozen versions and a bounded API budget.
4. Separate development scenarios from held-out evaluation; record all trials
   and uncertainty. Compare safety, usefulness, latency and review burden.
5. Produce a short technical report and demo with reproducibility instructions,
   limitations, negative findings and a concrete next research question.

The local runner and report are implemented. The real-model adapter, held-out
study, cost measurements and independent review above are proposed sprint work,
not completed experiments. A model quorum may challenge interpretations; it
cannot substitute for an independent execution record or confer permissions.

## Contribution and follow-up

The intended contribution is a small evaluation artifact that helps builders
notice weak boundaries before deploying agents. It connects practical systems
security to AI control evaluation without claiming to solve alignment.

After the sprint, test an actual MCP integration, invite reproduction, and
compare failure modes across models and controls. Publish only after normal
source, licensing and data review. The broader standards catalogue is context;
it does not need to become part of the sprint's experimental scope.
