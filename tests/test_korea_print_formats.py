import collections
import json
import pathlib
import unittest


class KoreaPrintFormatTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = pathlib.Path(__file__).resolve().parents[1]

    def load_print_format_json(self, *parts):
        path = self.repo_root.joinpath("hrms", "payroll", "print_format", *parts)
        with path.open() as handle:
            return json.load(handle)

    def test_salary_slip_korea_standard_exists_with_korean_sections(self):
        doc = self.load_print_format_json(
            "salary_slip_korea_standard",
            "salary_slip_korea_standard.json",
        )
        format_data = json.loads(doc["format_data"])

        self.assertEqual(doc["doc_type"], "Salary Slip")
        self.assertEqual(doc["module"], "Payroll")
        self.assertEqual(doc["name"], "Salary Slip Korea Standard")
        self.assertEqual(doc["default_print_language"], "ko")
        self.assertEqual(doc["print_format_builder"], 1)
        self.assertEqual(doc["show_section_headings"], 1)
        self.assertEqual(doc["standard"], "Yes")

        labels = [item.get("label") for item in format_data if item.get("label")]
        self.assertIn("지급 항목", labels)
        self.assertIn("공제 항목", labels)
        self.assertIn("한국 급여 요약", labels)
        self.assertIn("4대보험", labels)
        self.assertIn("세금", labels)
        self.assertIn("연말정산", labels)

        fieldnames = [item.get("fieldname") for item in format_data if item.get("fieldname")]
        duplicates = [fieldname for fieldname, count in collections.Counter(fieldnames).items() if count > 1]
        self.assertEqual(duplicates, [])

        fields = {item.get("fieldname"): item for item in format_data if item.get("fieldname")}
        self.assertEqual(
            [column["fieldname"] for column in fields["earnings"]["visible_columns"]],
            ["salary_component", "amount", "year_to_date"],
        )
        self.assertEqual(
            [column["fieldname"] for column in fields["deductions"]["visible_columns"]],
            ["salary_component", "amount", "year_to_date"],
        )

        expected_salary_fields = {
            "gross_pay",
            "kr_taxable_pay",
            "kr_nontaxable_pay",
            "net_pay",
            "kr_national_pension",
            "kr_health_insurance",
            "kr_longterm_care",
            "kr_employment_insurance",
            "kr_income_tax",
            "kr_local_income_tax",
            "kr_tax_method",
            "kr_prepaid_tax",
            "kr_determined_tax",
            "kr_adjustment_tax",
            "kr_year_end_settlement_kind",
            "kr_year_end_target_month",
        }
        self.assertTrue(expected_salary_fields.issubset(fields.keys()))

        heading_html = fields["print_heading_template"]["options"]
        self.assertIn("급여명세서", heading_html)


if __name__ == "__main__":
    unittest.main()
