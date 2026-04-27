import importlib.util
import pathlib
import sys
import types
import unittest


class FakeFrappeError(Exception):
    pass


class FakeDB:
    def __init__(self):
        self.exists_calls = []
        self.set_value_calls = []
        self.single_values = {}
        self.korea_calc_reference_run_ids = set()
        self.table_columns = {
            "Attendance": [
                "name",
                "employee",
                "attendance_date",
                "status",
                "shift",
                "working_hours",
                "custom_overtime_hours",
                "custom_night_hours",
                "custom_holiday_hours",
                "modified",
            ],
            "Employee": ["name", "employee_number", "employee_name", "visa_status_code"],
        }

    def exists(self, doctype, name):
        self.exists_calls.append((doctype, name))
        if doctype == "Salary Slip" and name == "SS-0001":
            return True
        if doctype == "Korea Calc Reference" and isinstance(name, dict):
            return name.get("run_id") in self.korea_calc_reference_run_ids
        return False

    def set_value(self, *args, **kwargs):
        self.set_value_calls.append((args, kwargs))

    def get_table_columns(self, doctype):
        return self.table_columns.get(doctype, [])


class FakeFrappeModule(types.SimpleNamespace):
    def __init__(self):
        super().__init__()
        self._employee_rows = []
        self._attendance_rows = []
        self._leave_rows = []
        self._comments = []
        self.get_all_calls = []
        self.db = FakeDB()
        self._ = lambda value: value
        self.whitelist = lambda *args, **kwargs: (lambda fn: fn)
        self.throw = self._throw
        self.parse_json = lambda value: value
        self.log_error = lambda *args, **kwargs: None
        self.get_traceback = lambda: "traceback"
        self.local = types.SimpleNamespace(form_dict={}, request=None)

    def _throw(self, message, exc=None):
        raise FakeFrappeError(message)

    def get_all(self, doctype, filters=None, fields=None, order_by=None, start=0, page_length=None, pluck=None):
        self.get_all_calls.append(
            {
                "doctype": doctype,
                "filters": filters,
                "fields": fields,
                "order_by": order_by,
                "start": start,
                "page_length": page_length,
                "pluck": pluck,
            }
        )
        rows = {
            "Employee": self._employee_rows,
            "Attendance": self._attendance_rows,
            "Leave Application": self._leave_rows,
            "Salary Slip": [],
        }[doctype]
        if pluck:
            return [row.get(pluck) for row in rows]
        if page_length is None:
            return list(rows[start:])
        return list(rows[start : start + page_length])

    def get_doc(self, payload):
        self._comments.append(payload)
        return types.SimpleNamespace(insert=lambda ignore_permissions=False: payload)


class KoreaIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fake_frappe = FakeFrappeModule()
        sys.modules["frappe"] = self.fake_frappe
        module_path = pathlib.Path(__file__).resolve().parents[1] / "hrms" / "api" / "korea_integration.py"
        spec = importlib.util.spec_from_file_location("test_korea_integration_module", module_path)
        self.module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(self.module)

    def tearDown(self):
        sys.modules.pop("frappe", None)

    def test_export_employee_master_normalizes_and_paginates(self):
        self.fake_frappe._employee_rows = [
            {
                "name": "EMP-0001",
                "employee_number": "1001",
                "employee_name": "Kim Worker",
                "company": "Winners",
                "branch": "Seoul",
                "department": "Ops",
                "designation": "Manager",
                "employment_type": "정규직",
                "date_of_joining": "2024-01-15",
                "relieving_date": None,
                "status": "Active",
                "modified": "2026-04-26 09:00:00",
            },
            {
                "name": "EMP-0002",
                "employee_number": "1002",
                "employee_name": "Lee Daily",
                "company": "Winners",
                "branch": "Busan",
                "department": "Store",
                "designation": "Crew",
                "employment_type": "계약직",
                "visa_status_code": "E-9",
                "date_of_joining": "2026-03-01",
                "relieving_date": None,
                "status": "Left",
                "modified": "2026-04-26 10:00:00",
            },
        ]

        result = self.module.export_employee_master(include_inactive=True, page=1, page_size=2)

        self.assertEqual(result["meta"], {"page": 1, "page_size": 2, "has_more": False})
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(result["data"][0]["employee_id"], "EMP-0001")
        self.assertEqual(result["data"][0]["employment_category"], "regular")
        self.assertEqual(result["data"][1]["employment_category"], "foreign_worker")
        self.assertEqual(result["data"][1]["visa_status_code"], "E-9")
        self.assertNotIn("address", result["data"][0])

    def test_export_time_and_leave_groups_records(self):
        self.fake_frappe._attendance_rows = [
            {
                "name": "ATT-0001",
                "employee": "EMP-0001",
                "attendance_date": "2026-04-01",
                "status": "Present",
                "shift": "Day",
                "working_hours": 8,
                "custom_overtime_hours": 2,
                "custom_night_hours": 1,
                "custom_holiday_hours": 0,
                "modified": "2026-04-01 20:00:00",
            }
        ]
        self.fake_frappe._leave_rows = [
            {
                "name": "LEAVE-0001",
                "employee": "EMP-0001",
                "leave_type": "연차",
                "from_date": "2026-04-10",
                "to_date": "2026-04-10",
                "half_day": 0,
                "half_day_date": None,
                "total_leave_days": 1,
                "status": "Approved",
                "modified": "2026-04-10 09:00:00",
            }
        ]

        result = self.module.export_time_and_leave(from_date="2026-04-01", to_date="2026-04-30")

        self.assertEqual(result["meta"], {"page": 1, "page_size": 100, "has_more": False})
        self.assertEqual(len(result["data"]), 1)
        employee_row = result["data"][0]
        self.assertEqual(employee_row["employee_id"], "EMP-0001")
        self.assertEqual(employee_row["attendance_records"][0]["regular_hours"], 8.0)
        self.assertEqual(employee_row["work_time_summary"]["overtime_hours_total"], 2.0)
        self.assertEqual(employee_row["leave_records"][0]["leave_type"], "연차")

    def test_export_time_and_leave_uses_bounded_page_length_for_queries(self):
        self.fake_frappe._employee_rows = [{"name": "EMP-0001"}]

        self.module.export_time_and_leave(
            from_date="2026-04-01",
            to_date="2026-04-30",
            company="Winners",
            branch="Seoul",
            page=2,
            page_size=10,
        )

        calls_by_doctype = {call["doctype"]: call for call in self.fake_frappe.get_all_calls}
        self.assertIsNotNone(calls_by_doctype["Employee"]["page_length"])
        self.assertIsNotNone(calls_by_doctype["Attendance"]["page_length"])
        self.assertIsNotNone(calls_by_doctype["Leave Application"]["page_length"])

    def test_import_payroll_result_rejects_pii_fields(self):
        with self.assertRaises(FakeFrappeError):
            self.module.import_payroll_result(
                payload={
                    "run_id": "RUN-1",
                    "employee_id": "EMP-0001",
                    "pay_year_month": "2026-04",
                    "taxable_items": [],
                    "non_taxable_items": [],
                    "social_insurance_deductions": {
                        "national_pension": 10,
                        "health_insurance": 20,
                        "long_term_care_insurance": 3,
                        "employment_insurance": 4,
                    },
                    "withholding_tax": {"income_tax": 30, "local_income_tax": 3},
                    "net_pay": 1000,
                    "resident_registration_number": "900101-1234567",
                }
            )

    def test_import_payroll_result_parses_json_payload_and_rejects_unknown_fields(self):
        self.fake_frappe.local.form_dict = {
            "payload": '{"run_id":"RUN-1","employee_id":"EMP-0001","pay_year_month":"2026-04","taxable_items":[],"non_taxable_items":[],"social_insurance_deductions":{"national_pension":10,"health_insurance":20,"long_term_care_insurance":3,"employment_insurance":4},"withholding_tax":{"income_tax":30,"local_income_tax":3},"net_pay":1000,"unexpected":"x"}'
        }

        with self.assertRaises(FakeFrappeError):
            self.module.import_payroll_result()

    def test_import_payroll_result_rejects_duplicate_run_id(self):
        self.fake_frappe.db.korea_calc_reference_run_ids.add("RUN-1")

        with self.assertRaises(FakeFrappeError):
            self.module.import_payroll_result(
                payload={
                    "run_id": "RUN-1",
                    "employee_id": "EMP-0001",
                    "pay_year_month": "2026-04",
                    "taxable_items": [],
                    "non_taxable_items": [],
                    "social_insurance_deductions": {
                        "national_pension": 10,
                        "health_insurance": 20,
                        "long_term_care_insurance": 3,
                        "employment_insurance": 4,
                    },
                    "withholding_tax": {"income_tax": 30, "local_income_tax": 3},
                    "net_pay": 1000,
                }
            )

        self.assertIn(("Korea Calc Reference", {"run_id": "RUN-1"}), self.fake_frappe.db.exists_calls)

    def test_as_float_raises_when_frappe_throw_returns_unexpectedly(self):
        self.fake_frappe.throw = lambda message, exc=None: None

        with self.assertRaises(RuntimeError):
            self.module._as_float("not-a-number")

    def test_import_payroll_result_links_salary_slip_when_external_ref_exists(self):
        result = self.module.import_payroll_result(
            payload={
                "run_id": "RUN-1",
                "employee_id": "EMP-0001",
                "pay_year_month": "2026-04",
                "salary_slip_external_ref": "SS-0001",
                "taxable_items": [{"code": "BASE", "label": "기본급", "amount": 2000}],
                "non_taxable_items": [],
                "social_insurance_deductions": {
                    "national_pension": 10,
                    "health_insurance": 20,
                    "long_term_care_insurance": 3,
                    "employment_insurance": 4,
                },
                "withholding_tax": {"income_tax": 30, "local_income_tax": 3},
                "gross_pay": 2000,
                "total_deduction": 67,
                "net_pay": 1933,
            }
        )

        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["salary_slip"], "SS-0001")
        self.assertEqual(len(self.fake_frappe._comments), 1)
        self.assertEqual(self.fake_frappe._comments[0]["reference_name"], "SS-0001")


if __name__ == "__main__":
    unittest.main()
