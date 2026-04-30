import pathlib
import unittest


class KoreaPrivacyContractTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = pathlib.Path(__file__).resolve().parents[1]

    def test_contract_explicitly_defers_live_privacy_broker_in_phase2_pilot(self):
        contract_text = (
            self.repo_root / "docs" / "integration" / "frappe-side-contract.md"
        ).read_text()

        self.assertIn("Phase 2 pilot defer note", contract_text)
        self.assertIn("privacy_broker live integration is deferred", contract_text)
        self.assertIn("Frappe runtime does not call privacy_broker in this pilot", contract_text)
        self.assertIn("manual or external secure-store lookup remains outside this repo", contract_text)

    def test_runbook_lists_privacy_broker_defer_as_pilot_scope_rule(self):
        runbook_text = (
            self.repo_root / "docs" / "runbooks" / "korea-phase2-runtime-gate-and-pilot-smoke.md"
        ).read_text()

        self.assertIn("privacy_broker live integration is deferred for this pilot", runbook_text)
        self.assertIn("do not hot-deploy placeholder broker code", runbook_text)
        self.assertIn("PII lookup stays outside Frappe runtime", runbook_text)


if __name__ == "__main__":
    unittest.main()
