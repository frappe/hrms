"""
Tests for Payroll Setup Demo Data Scripts

Lightweight test suite centered on verifying that the payroll data was
correctly added to the module. Includes basic JSON validation (runs standalone)
and database verification tests (requires Frappe context).

Run standalone JSON tests:
    cd hrms/demo_data && python -m unittest test_payroll_setup -v

Run DB verification tests (inside Docker):
    podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && ./env/bin/python -m pytest apps/hrms/hrms/demo_data/test_payroll_setup.py -v'
"""

import json
import os
import unittest


PAYROLL_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employee_payroll.json")


class TestPayrollJsonValidation(unittest.TestCase):
    """Basic sanity checks on the employee_payroll.json file."""

    @classmethod
    def setUpClass(cls):
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)
        cls.components = cls.data.get("salary_components", [])
        cls.structures = cls.data.get("salary_structures", [])

    def test_required_top_level_keys(self):
        """JSON must contain all required top-level keys."""
        required = [
            "config", "executive_designations", "default_components_to_delete",
            "salary_components", "salary_structures", "income_tax_slabs",
            "employee_salaries", "metadata",
        ]
        for key in required:
            self.assertIn(key, self.data, f"Missing top-level key: '{key}'")

    def test_salary_components_count(self):
        """There must be exactly 8 salary components."""
        self.assertEqual(len(self.components), 8)

    def test_salary_structures_reference_valid_components(self):
        """All components referenced in structures must exist in salary_components."""
        comp_names = {c["name"] for c in self.components}
        for struct in self.structures:
            for row in struct.get("earnings", []) + struct.get("deductions", []):
                self.assertIn(row["salary_component"], comp_names,
                              f"Structure '{struct['name']}' references unknown component: '{row['salary_component']}'")

    def test_income_tax_slabs_contiguous_and_progressive(self):
        """Tax slabs must be contiguous and have progressive rates."""
        slabs = self.data.get("income_tax_slabs", [])
        self.assertGreater(len(slabs), 0)
        self.assertEqual(slabs[0]["from_amount"], 0)
        for i in range(1, len(slabs)):
            self.assertEqual(slabs[i]["from_amount"], slabs[i - 1]["to_amount"])
            self.assertGreaterEqual(slabs[i]["percent_deduction"], slabs[i - 1]["percent_deduction"])

    def test_income_tax_federal_in_both_structures(self):
        """Income Tax Federal must appear in deductions of both structures."""
        for struct in self.structures:
            deduction_names = [d["salary_component"] for d in struct.get("deductions", [])]
            self.assertIn("Income Tax Federal", deduction_names,
                          f"Structure '{struct['name']}' missing Income Tax Federal")

    def test_structure_detail_rows_carry_formulas(self):
        """Detail rows with amount_based_on_formula=1 must have a formula field."""
        for struct in self.structures:
            for row in struct.get("earnings", []) + struct.get("deductions", []):
                if row.get("amount_based_on_formula") == 1:
                    self.assertTrue(row.get("formula"),
                                    f"Structure '{struct['name']}' detail '{row['salary_component']}' missing formula")

    def test_script_uses_load_json_from_utils(self):
        """payroll_setup.py must use load_json from utils, not raw json.load."""
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payroll_setup.py")
        with open(script_path, "r") as f:
            content = f.read()
        self.assertIn("from hrms.demo_data.utils import load_json", content)
        self.assertNotIn("import json", content)


class TestDatabaseVerification(unittest.TestCase):
    """Verify payroll data was correctly added to the database.

    These tests require Frappe context and validate that the script
    created the expected records. Run with:
        podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && ./env/bin/python -m pytest apps/hrms/hrms/demo_data/test_payroll_setup.py -v'
    """

    COMPANY = "NovaSoft"

    @classmethod
    def setUpClass(cls):
        try:
            import frappe
        except ImportError:
            raise unittest.SkipTest("frappe not installed")

        # Derive bench path from the test file location.
        # File: <bench>/apps/hrms/hrms/demo_data/test_payroll_setup.py
        test_dir = os.path.dirname(os.path.abspath(__file__))
        bench_path = os.path.abspath(os.path.join(test_dir, "..", "..", "..", ".."))
        sites_path = os.path.join(bench_path, "sites")

        if not os.path.isdir(sites_path):
            raise unittest.SkipTest(f"Sites directory not found: {sites_path}")

        # Frappe resolves log paths relative to CWD (e.g. "../logs/database.log").
        # Bench processes normally run from <bench>/sites so that "../logs" points
        # to <bench>/logs. We replicate that here so the logger can find its files.
        os.chdir(sites_path)

        frappe.init(site="hrms.localhost", sites_path=sites_path)
        frappe.connect()
        frappe.set_user("Administrator")

        cls.frappe = frappe
        with open(PAYROLL_JSON_PATH, "r") as f:
            cls.data = json.load(f)

    def test_verify_salary_components(self):
        """Verify all custom salary components exist in the database."""
        expected = [c["name"] for c in self.data.get("salary_components", [])]
        for name in expected:
            self.assertTrue(
                self.frappe.db.exists("Salary Component", name),
                f"Salary Component '{name}' not found in database",
            )

    def test_verify_salary_structures(self):
        """Verify salary structures exist and are submitted."""
        for struct in self.data.get("salary_structures", []):
            name = struct["name"]
            self.assertTrue(
                self.frappe.db.exists("Salary Structure", name),
                f"Salary Structure '{name}' not found in database",
            )
            doc = self.frappe.get_doc("Salary Structure", name)
            self.assertEqual(doc.docstatus, 1, f"Salary Structure '{name}' is not submitted")
            self.assertEqual(doc.is_active, "Yes", f"Salary Structure '{name}' is not active")

    def test_verify_structure_assignments(self):
        """Verify salary structure assignments exist with non-zero base salary."""
        assignments = self.frappe.get_all(
            "Salary Structure Assignment",
            filters={"company": self.COMPANY, "docstatus": 1},
            fields=["employee", "employee_name", "salary_structure", "base"],
        )
        self.assertGreater(len(assignments), 0, "No salary structure assignments found")
        for a in assignments:
            self.assertGreater(
                a.base, 0,
                f"Assignment for {a.employee_name} has zero base salary",
            )

    def test_verify_salary_slips(self):
        """Verify salary slips exist with non-zero gross pay and net pay."""
        slips = self.frappe.get_all(
            "Salary Slip",
            filters={"company": self.COMPANY},
            fields=["employee", "employee_name", "gross_pay", "total_deduction", "net_pay"],
        )
        self.assertGreater(len(slips), 0, "No salary slips found")
        for slip in slips:
            self.assertGreater(
                slip.gross_pay, 0,
                f"Salary slip for {slip.employee_name} has zero gross pay",
            )
            self.assertGreater(
                slip.net_pay, 0,
                f"Salary slip for {slip.employee_name} has zero net pay",
            )

    def test_verify_income_tax_slab(self):
        """Verify income tax slab exists with the correct number of brackets."""
        config = self.data.get("config", {})
        fiscal_year = config.get("fiscal_year", "2025")
        slab_name = f"Federal Tax {fiscal_year} - {self.COMPANY}"
        self.assertTrue(
            self.frappe.db.exists("Income Tax Slab", slab_name),
            f"Income Tax Slab '{slab_name}' not found in database",
        )
        doc = self.frappe.get_doc("Income Tax Slab", slab_name)
        expected_brackets = len(self.data.get("income_tax_slabs", []))
        self.assertEqual(
            len(doc.slabs), expected_brackets,
            f"Expected {expected_brackets} tax brackets, got {len(doc.slabs)}",
        )

    def test_verify_payroll_year(self):
        """Verify fiscal year exists and is associated with the company."""
        fiscal_year = self.data.get("config", {}).get("fiscal_year", "2025")
        self.assertTrue(
            self.frappe.db.exists("Fiscal Year", fiscal_year),
            f"Fiscal Year '{fiscal_year}' not found in database",
        )
        doc = self.frappe.get_doc("Fiscal Year", fiscal_year)
        companies = [c.company for c in doc.companies]
        self.assertIn(
            self.COMPANY, companies,
            f"Company '{self.COMPANY}' not associated with Fiscal Year '{fiscal_year}'",
        )


if __name__ == "__main__":
    unittest.main()
