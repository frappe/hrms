import importlib.util
import pathlib
import sys
import types
import unittest


class KoreaSalarySlipHookTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = pathlib.Path(__file__).resolve().parents[1]
        self.original_modules = sys.modules.copy()

        class FakeDB:
            def __init__(self):
                self.company_country = {}
                self.employee_values = {}
                self.calls = []

            def get_value(self, doctype, name, fieldname, as_dict=False, cache=False):
                self.calls.append((doctype, name, fieldname, as_dict, cache))
                if doctype == "Company" and fieldname == "country":
                    return self.company_country.get(name)
                if doctype == "Employee":
                    value = self.employee_values.get(name, {})
                    if as_dict:
                        return types.SimpleNamespace(**value)
                    return value
                return None

        self.fake_db = FakeDB()

        frappe_module = types.ModuleType("frappe")
        frappe_module.db = self.fake_db
        sys.modules["frappe"] = frappe_module

        module_path = (
            self.repo_root
            / "hrms"
            / "payroll"
            / "doctype"
            / "salary_slip"
            / "korea_salary_slip.py"
        )
        spec = importlib.util.spec_from_file_location("test_korea_salary_slip", module_path)
        self.module = importlib.util.module_from_spec(spec)
        self.module_types = types
        assert spec.loader is not None
        self.spec = spec

    def tearDown(self):
        sys.modules.clear()
        sys.modules.update(self.original_modules)

    def load_module(self):
        self.spec.loader.exec_module(self.module)
        return self.module

    def test_apply_korea_salary_slip_fields_noops_for_non_korea_company(self):
        self.fake_db.company_country["ACME"] = "United States"
        module = self.load_module()
        doc = types.SimpleNamespace(
            company="ACME",
            employee="EMP-0001",
            gross_pay=3000000,
            non_taxable_earnings=200000,
            total_deduction=400000,
            current_month_income_tax=120000,
            kr_tax_method=None,
        )

        module.apply_korea_salary_slip_fields(doc)

        self.assertFalse(hasattr(doc, "kr_taxable_pay"))
        self.assertIsNone(doc.kr_tax_method)

    def test_apply_korea_salary_slip_fields_populates_phase2_baseline_for_korea(self):
        self.fake_db.company_country["WINNERS"] = "South Korea"
        self.fake_db.employee_values["EMP-0001"] = {
            "kr_foreign_flat_tax": 0,
            "kr_withholding_rate": 100,
        }
        module = self.load_module()
        doc = types.SimpleNamespace(
            company="WINNERS",
            employee="EMP-0001",
            gross_pay=3500000,
            non_taxable_earnings=200000,
            total_deduction=500000,
            current_month_income_tax=140000,
        )

        module.apply_korea_salary_slip_fields(doc)

        self.assertEqual(doc.kr_tax_method, "간이세액표")
        self.assertEqual(doc.kr_taxable_pay, 3300000)
        self.assertEqual(doc.kr_nontaxable_pay, 200000)
        self.assertEqual(doc.kr_income_tax, 140000)
        self.assertEqual(doc.kr_total_deductions, 500000)

    def test_apply_korea_salary_slip_fields_uses_foreign_flat_tax_for_tax_method(self):
        self.fake_db.company_country["WINNERS"] = "South Korea"
        self.fake_db.employee_values["EMP-0002"] = {
            "kr_foreign_flat_tax": 1,
            "kr_withholding_rate": 100,
        }
        module = self.load_module()
        doc = types.SimpleNamespace(
            company="WINNERS",
            employee="EMP-0002",
            gross_pay=4200000,
            non_taxable_earnings=0,
            total_deduction=630000,
            current_month_income_tax=190000,
        )

        module.apply_korea_salary_slip_fields(doc)

        self.assertEqual(doc.kr_tax_method, "19% flat")
        self.assertEqual(doc.kr_taxable_pay, 4200000)
        self.assertEqual(doc.kr_nontaxable_pay, 0)
        self.assertEqual(doc.kr_income_tax, 190000)
        self.assertEqual(doc.kr_total_deductions, 630000)

    def test_hooks_register_salary_slip_validate_handler(self):
        hooks_path = self.repo_root / "hrms" / "hooks.py"
        hooks_text = hooks_path.read_text()

        self.assertIn('"Salary Slip": {', hooks_text)
        self.assertIn(
            '"validate": "hrms.payroll.doctype.salary_slip.korea_salary_slip.apply_korea_salary_slip_fields"',
            hooks_text,
        )


if __name__ == "__main__":
    unittest.main()
