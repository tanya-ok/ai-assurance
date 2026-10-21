# SPDX-FileCopyrightText: 2026 Tanya Babitskaya
# SPDX-License-Identifier: Apache-2.0
"""State-change and input-boundary tests for the local control experiment."""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from control_experiment import (
    READ,
    RECORDS,
    WRITE,
    Broker,
    Context,
    digest,
    experiment,
    profile_findings,
)


class ControlExperimentTests(unittest.TestCase):
    def test_unsafe_baseline_and_deny_all_do_not_look_successful(self):
        report = experiment()
        safe = report["summaries"]["bounded"]
        self.assertEqual(safe["adversarial_outcomes_satisfied"], safe["adversarial_scenarios"])
        self.assertEqual(safe["legitimate_tasks_completed"], safe["legitimate_tasks"])
        self.assertLess(
            report["summaries"]["unrestricted"]["adversarial_outcomes_satisfied"],
            safe["adversarial_scenarios"],
        )
        self.assertEqual(report["summaries"]["deny-all"]["legitimate_tasks_completed"], 0)
        self.assertEqual(report["model_behavior"], "not_verified")
        self.assertEqual(report["hipaa_compliance"], "not_verified")

    def test_denied_write_leaves_store_unchanged(self):
        broker = Broker(Context())
        before = copy.deepcopy(broker.records)
        self.assertEqual(broker.execute(WRITE)["decision"], "deny")
        self.assertEqual(broker.records, before)

    def test_authorization_is_exact_and_consumed(self):
        broker = Broker(Context(approved=frozenset({digest(WRITE)})))
        self.assertEqual(broker.execute({**WRITE, "resource": "demo-b"})["decision"], "deny")
        self.assertEqual(broker.execute({**WRITE, "value": "scheduled"})["decision"], "deny")
        self.assertEqual(broker.execute(WRITE)["decision"], "allow")
        self.assertEqual(broker.records["demo-a"]["status"], "reviewed")
        self.assertEqual(broker.execute(WRITE)["decision"], "deny")
        self.assertEqual(broker.records["demo-b"], RECORDS["demo-b"])

    def test_cancellation_revokes_preapproved_action(self):
        broker = Broker(Context(approved=frozenset({digest(WRITE)}), cancelled=True))
        self.assertEqual(broker.execute(WRITE)["decision"], "deny")
        self.assertEqual(broker.records, RECORDS)

    def test_untrusted_arguments_never_authorize_or_log_payload(self):
        broker = Broker(Context())
        sentinel = "UNTRUSTED_SECRET_SENTINEL"
        for key in ("approved", "instructions", "policy", "session", "audit"):
            proposal = {**WRITE, key: sentinel}
            self.assertEqual(broker.execute(proposal)["decision"], "deny")
        self.assertNotIn(sentinel, json.dumps(broker.audit))
        self.assertNotIn("private", json.dumps(broker.audit))
        self.assertEqual(broker.records, RECORDS)

    def test_malformed_nested_inputs_deny_without_exception_or_mutation(self):
        broker = Broker(Context())
        proposals = [
            [],
            None,
            {"action": [], "resource": "demo-a"},
            {"action": "read", "resource": {}},
            {**READ, "fields": [[]]},
            {**READ, "fields": []},
            {**WRITE, "value": {}},
            {**READ, "fields": ["missing"]},
        ]
        for proposal in proposals:
            with self.subTest(proposal=proposal):
                self.assertEqual(broker.execute(proposal)["decision"], "deny")
        self.assertEqual(broker.records, RECORDS)
        self.assertEqual(len(broker.audit), len(proposals))

    def test_unknown_mode_and_export_grants_do_not_enable_export(self):
        proposal = {"action": "export", "resource": "demo-a", "value": "reviewed"}
        for mode in ("invalid", "bounded"):
            broker = Broker(Context(actions=frozenset({"export"})), mode)
            self.assertEqual(broker.execute(proposal)["decision"], "deny")

    def test_data_returned_is_only_granted_fields(self):
        broker = Broker(Context())
        output = broker.execute(READ)
        self.assertEqual(output["data"], {"status": "scheduled", "note": "synthetic note"})
        self.assertEqual(broker.execute({**READ, "fields": ["private"]})["decision"], "deny")
        self.assertEqual(len(broker.audit), 2)

    def test_repeated_experiments_have_identical_outcomes_and_input_hashes(self):
        first, second = experiment(), experiment()
        for key in ("summaries", "results", "suite_sha256", "source_sha256"):
            self.assertEqual(first[key], second[key])


class EvidenceBoundaryTests(unittest.TestCase):
    def test_technical_pass_does_not_verify_organizational_or_model_requirements(self):
        report = experiment()
        statuses = {x["id"]: x["status"] for x in report["findings"]}
        self.assertEqual(statuses["local-resource-grants"], "supported")
        for control in (
            "organizational-risk-analysis",
            "provider-agreements",
            "identity-and-transmission",
            "durable-audit-and-recovery",
            "model-behavior-evaluation",
        ):
            self.assertEqual(statuses[control], "not_verified")

    def test_missing_scenario_refused_and_observed_failure_remains_gap(self):
        profile = {
            "schema": 1,
            "scope": "synthetic-healthcare-local-v1",
            "requirements": [
                {
                    "id": "local-read",
                    "area": "security",
                    "source": "https://example.org",
                    "scenarios": ["known"],
                    "limit": "fixture only",
                }
            ],
        }
        rows = [{"scenario": "known", "mode": "bounded", "passed": False}]
        self.assertEqual(profile_findings(profile, rows)[0]["status"], "gap")
        profile["requirements"][0]["scenarios"] = ["missing"]
        with self.assertRaises(ValueError):
            profile_findings(profile, rows)


if __name__ == "__main__":
    unittest.main()
