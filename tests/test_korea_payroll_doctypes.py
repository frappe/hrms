import importlib.util
import json
import pathlib
import sys
import types
import unittest


class KoreaPayrollDocTypeScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = pathlib.Path(__file__).resolve().parents[1]
        self.original_modules = sys.modules.copy()

        document_module = types.ModuleType("frappe.model.document")
        document_module.Document = type("Document", (), {})
        sys.modules["frappe"] = types.ModuleType("frappe")
        sys.modules["frappe.model"] = types.ModuleType("frappe.model")
        sys.modules["frappe.model.document"] = document_module

    def tearDown(self):
        sys.modules.clear()
        sys.modules.update(self.original_modules)

    def load_doctype_json(self, *parts):
        path = self.repo_root.joinpath("hrms", "payroll", "doctype", *parts)
        with path.open() as handle:
            return json.load(handle)

    def load_doctype_module(self, *parts):
        path = self.repo_root.joinpath("hrms", "payroll", "doctype", *parts)
        spec = importlib.util.spec_from_file_location("test_doctype_module", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_korea_insurance_rates_scaffold_exists_with_effective_fields(self):
        doc = self.load_doctype_json(
            "korea_insurance_rates",
            "korea_insurance_rates.json",
        )
        fields = {field["fieldname"]: field for field in doc["fields"]}

        expected = {
            "effective_from",
            "national_pension_rate",
            "pension_upper_limit",
            "pension_lower_limit",
            "health_insurance_rate",
            "longterm_care_rate",
            "employment_insurance_rate",
            "min_wage_hourly",
        }

        self.assertEqual(doc["module"], "Payroll")
        self.assertEqual(doc["name"], "Korea Insurance Rates")
        self.assertTrue(expected.issubset(fields.keys()))
        self.assertEqual(fields["effective_from"]["fieldtype"], "Date")
        self.assertEqual(fields["national_pension_rate"]["fieldtype"], "Percent")
        self.assertEqual(fields["min_wage_hourly"]["fieldtype"], "Currency")

        module = self.load_doctype_module(
            "korea_insurance_rates",
            "korea_insurance_rates.py",
        )
        self.assertTrue(hasattr(module, "KoreaInsuranceRates"))

    def test_korea_tax_table_scaffold_exists_with_dependents_columns(self):
        doc = self.load_doctype_json(
            "korea_tax_table",
            "korea_tax_table.json",
        )
        fields = {field["fieldname"]: field for field in doc["fields"]}

        expected = {
            "year",
            "salary_from",
            "salary_to",
            "dep_1",
            "dep_2",
            "dep_3",
            "dep_4",
            "dep_5",
            "dep_6",
            "dep_7",
            "dep_8",
            "dep_9",
            "dep_10",
            "dep_11",
        }

        self.assertEqual(doc["module"], "Payroll")
        self.assertEqual(doc["name"], "Korea Tax Table")
        self.assertTrue(expected.issubset(fields.keys()))
        self.assertEqual(fields["year"]["fieldtype"], "Int")
        self.assertEqual(fields["salary_from"]["fieldtype"], "Currency")
        self.assertEqual(fields["dep_11"]["fieldtype"], "Currency")

        module = self.load_doctype_module(
            "korea_tax_table",
            "korea_tax_table.py",
        )
        self.assertTrue(hasattr(module, "KoreaTaxTable"))

    def test_korea_salary_slip_extension_scaffold_exists_with_payroll_summary_fields(self):
        doc = self.load_doctype_json(
            "korea_salary_slip_extension",
            "korea_salary_slip_extension.json",
        )
        fields = {field["fieldname"]: field for field in doc["fields"]}

        expected = {
            "salary_slip",
            "employee",
            "pay_year_month",
            "taxable_total",
            "non_taxable_total",
            "national_pension",
            "health_insurance",
            "long_term_care_insurance",
            "employment_insurance",
            "income_tax",
            "local_income_tax",
            "net_pay",
            "tax_method",
            "linked_calc_reference",
        }

        self.assertEqual(doc["module"], "Payroll")
        self.assertEqual(doc["name"], "Korea Salary Slip Extension")
        self.assertEqual(doc["autoname"], "field:salary_slip")
        self.assertEqual(doc["title_field"], "salary_slip")
        self.assertTrue(expected.issubset(fields.keys()))
        self.assertEqual(fields["salary_slip"]["fieldtype"], "Link")
        self.assertEqual(fields["salary_slip"]["options"], "Salary Slip")
        self.assertEqual(fields["salary_slip"]["reqd"], 1)
        self.assertEqual(fields["salary_slip"]["unique"], 1)
        self.assertEqual(fields["taxable_total"]["fieldtype"], "Currency")
        self.assertEqual(fields["tax_method"]["fieldtype"], "Select")
        self.assertEqual(fields["linked_calc_reference"]["options"], "Korea Calc Reference")

        employee_permissions = [perm for perm in doc["permissions"] if perm["role"] == "Employee"]
        self.assertEqual(employee_permissions, [])
        self.assertTrue(any(perm["role"] == "System Manager" for perm in doc["permissions"]))
        self.assertTrue(any(perm["role"] == "HR Manager" for perm in doc["permissions"]))

        module = self.load_doctype_module(
            "korea_salary_slip_extension",
            "korea_salary_slip_extension.py",
        )
        self.assertTrue(hasattr(module, "KoreaSalarySlipExtension"))

    def test_korea_severance_slip_scaffold_exists_with_audit_fields(self):
        doc = self.load_doctype_json(
            "korea_severance_slip",
            "korea_severance_slip.json",
        )
        fields = {field["fieldname"]: field for field in doc["fields"]}

        expected = {
            "employee",
            "retirement_date",
            "linked_salary_slip",
            "average_wage",
            "service_years",
            "severance_pay",
            "severance_income_tax",
            "local_income_tax",
            "net_pay",
            "external_run_id",
            "engine_version",
            "ruleset_version",
            "linked_calc_reference",
        }

        self.assertEqual(doc["module"], "Payroll")
        self.assertEqual(doc["name"], "Korea Severance Slip")
        self.assertEqual(doc["autoname"], "field:external_run_id")
        self.assertEqual(doc["title_field"], "external_run_id")
        self.assertTrue(expected.issubset(fields.keys()))
        self.assertEqual(fields["employee"]["fieldtype"], "Link")
        self.assertEqual(fields["employee"]["options"], "Employee")
        self.assertEqual(fields["retirement_date"]["fieldtype"], "Date")
        self.assertEqual(fields["average_wage"]["fieldtype"], "Currency")
        self.assertEqual(fields["service_years"]["fieldtype"], "Float")
        self.assertEqual(fields["external_run_id"]["fieldtype"], "Data")
        self.assertEqual(fields["external_run_id"]["reqd"], 1)
        self.assertEqual(fields["external_run_id"]["unique"], 1)
        self.assertEqual(fields["linked_calc_reference"]["options"], "Korea Calc Reference")

        employee_permissions = [perm for perm in doc["permissions"] if perm["role"] == "Employee"]
        self.assertEqual(employee_permissions, [])
        self.assertTrue(any(perm["role"] == "System Manager" for perm in doc["permissions"]))
        self.assertTrue(any(perm["role"] == "HR Manager" for perm in doc["permissions"]))

        module = self.load_doctype_module(
            "korea_severance_slip",
            "korea_severance_slip.py",
        )
        self.assertTrue(hasattr(module, "KoreaSeveranceSlip"))


if __name__ == "__main__":
    unittest.main()
