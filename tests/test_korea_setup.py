import importlib.util
import pathlib
import sys
import types
import unittest


class KoreaSetupCustomFieldsTests(unittest.TestCase):
    def setUp(self):
        self.original_modules = sys.modules.copy()

        frappe_module = types.ModuleType("frappe")
        frappe_module.db = types.SimpleNamespace(delete=lambda *args, **kwargs: None)
        frappe_module.clear_cache = lambda *args, **kwargs: None
        frappe_module.get_doc = lambda *args, **kwargs: types.SimpleNamespace(
            append=lambda *a, **k: None,
            save=lambda: None,
        )
        sys.modules["frappe"] = frappe_module

        custom_field_module = types.ModuleType("frappe.custom.doctype.custom_field.custom_field")
        custom_field_module.create_custom_fields = lambda *args, **kwargs: None
        sys.modules["frappe.custom"] = types.ModuleType("frappe.custom")
        sys.modules["frappe.custom.doctype"] = types.ModuleType("frappe.custom.doctype")
        sys.modules["frappe.custom.doctype.custom_field"] = types.ModuleType(
            "frappe.custom.doctype.custom_field"
        )
        sys.modules["frappe.custom.doctype.custom_field.custom_field"] = custom_field_module

        install_fixtures_module = types.ModuleType(
            "frappe.desk.page.setup_wizard.install_fixtures"
        )
        install_fixtures_module._ = lambda value: value
        setup_wizard_module = types.ModuleType("frappe.desk.page.setup_wizard.setup_wizard")
        setup_wizard_module.make_records = lambda *args, **kwargs: None
        sys.modules["frappe.desk"] = types.ModuleType("frappe.desk")
        sys.modules["frappe.desk.page"] = types.ModuleType("frappe.desk.page")
        sys.modules["frappe.desk.page.setup_wizard"] = types.ModuleType(
            "frappe.desk.page.setup_wizard"
        )
        sys.modules[
            "frappe.desk.page.setup_wizard.install_fixtures"
        ] = install_fixtures_module
        sys.modules["frappe.desk.page.setup_wizard.setup_wizard"] = setup_wizard_module

        permissions_module = types.ModuleType("frappe.permissions")
        permissions_module.add_permission = lambda *args, **kwargs: None
        permissions_module.update_permission_property = lambda *args, **kwargs: None
        sys.modules["frappe.permissions"] = permissions_module

        overrides_company_module = types.ModuleType("hrms.overrides.company")
        overrides_company_module.delete_company_fixtures = lambda *args, **kwargs: None
        sys.modules["hrms"] = types.ModuleType("hrms")
        sys.modules["hrms.overrides"] = types.ModuleType("hrms.overrides")
        sys.modules["hrms.overrides.company"] = overrides_company_module

        module_path = (
            pathlib.Path(__file__).resolve().parents[1] / "hrms" / "setup.py"
        )
        spec = importlib.util.spec_from_file_location("test_hrms_setup", module_path)
        self.module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(self.module)

    def tearDown(self):
        sys.modules.clear()
        sys.modules.update(self.original_modules)

    def test_get_custom_fields_includes_korea_employee_phase2_fields(self):
        custom_fields = self.module.get_custom_fields()
        employee_fields = {
            field["fieldname"]: field for field in custom_fields.get("Employee", [])
        }

        expected = {
            "kr_payroll_section",
            "kr_dependents_count",
            "kr_withholding_rate",
            "kr_foreign_flat_tax",
            "kr_pension_notified_amount",
            "kr_pension_exempt",
            "kr_employ_ins_exempt",
            "kr_visa_type",
            "kr_pension_agreement",
            "kr_foreign_employ_exempt",
        }

        self.assertTrue(expected.issubset(employee_fields.keys()))
        self.assertEqual(employee_fields["kr_dependents_count"]["fieldtype"], "Int")
        self.assertEqual(employee_fields["kr_withholding_rate"]["fieldtype"], "Percent")
        self.assertEqual(employee_fields["kr_pension_exempt"]["fieldtype"], "Check")

    def test_get_custom_fields_includes_korea_salary_slip_phase2_fields(self):
        custom_fields = self.module.get_custom_fields()
        salary_slip_fields = {
            field["fieldname"]: field for field in custom_fields.get("Salary Slip", [])
        }

        expected = {
            "kr_insurance_detail_section",
            "kr_national_pension",
            "kr_health_insurance",
            "kr_longterm_care",
            "kr_employment_insurance",
            "kr_insurance_employer_total",
            "kr_tax_detail_section",
            "kr_income_tax",
            "kr_local_income_tax",
            "kr_tax_method",
            "kr_summary_section",
            "kr_taxable_pay",
            "kr_nontaxable_pay",
            "kr_total_deductions",
            "kr_year_end_section",
            "kr_prepaid_tax",
            "kr_determined_tax",
            "kr_adjustment_tax",
        }

        self.assertTrue(expected.issubset(salary_slip_fields.keys()))
        self.assertEqual(salary_slip_fields["kr_national_pension"]["fieldtype"], "Currency")
        self.assertEqual(salary_slip_fields["kr_tax_method"]["fieldtype"], "Select")
        self.assertIn("간이세액표", salary_slip_fields["kr_tax_method"]["options"])

    def test_get_custom_fields_places_korea_salary_slip_fields_in_two_column_sections(self):
        custom_fields = self.module.get_custom_fields()
        salary_slip_fields = {
            field["fieldname"]: field for field in custom_fields.get("Salary Slip", [])
        }

        self.assertEqual(salary_slip_fields["kr_insurance_employee_column_break"]["fieldtype"], "Column Break")
        self.assertEqual(
            salary_slip_fields["kr_insurance_employee_column_break"]["insert_after"],
            "kr_health_insurance",
        )
        self.assertEqual(salary_slip_fields["kr_tax_column_break"]["fieldtype"], "Column Break")
        self.assertEqual(salary_slip_fields["kr_tax_column_break"]["insert_after"], "kr_income_tax")
        self.assertEqual(salary_slip_fields["kr_summary_column_break"]["fieldtype"], "Column Break")
        self.assertEqual(salary_slip_fields["kr_summary_column_break"]["insert_after"], "kr_taxable_pay")
        self.assertEqual(salary_slip_fields["kr_year_end_column_break"]["fieldtype"], "Column Break")
        self.assertEqual(
            salary_slip_fields["kr_year_end_column_break"]["insert_after"],
            "kr_adjustment_tax",
        )

    def test_korean_locale_file_covers_korea_payroll_labels(self):
        locale_path = pathlib.Path(__file__).resolve().parents[1] / "hrms" / "locale" / "ko.po"
        locale_text = locale_path.read_text()

        self.assertIn('msgid "Korea Payroll"', locale_text)
        self.assertIn('msgstr "한국 급여"', locale_text)
        self.assertIn('msgid "Korea Insurance Detail"', locale_text)
        self.assertIn('msgstr "4대보험 상세"', locale_text)
        self.assertIn('msgid "Korea Tax Detail"', locale_text)
        self.assertIn('msgstr "세금 상세"', locale_text)
        self.assertIn('msgid "Korea Payroll Summary"', locale_text)
        self.assertIn('msgstr "한국 급여 요약"', locale_text)
        self.assertIn('msgid "Korea Year End Settlement"', locale_text)
        self.assertIn('msgstr "연말정산"', locale_text)


if __name__ == "__main__":
    unittest.main()
