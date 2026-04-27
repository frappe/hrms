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


if __name__ == "__main__":
    unittest.main()
