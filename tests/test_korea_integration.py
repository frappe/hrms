import importlib.util
import pathlib
import sys
import types
import unittest
from unittest import mock


class FakeFrappeError(Exception):
    pass


class FakeDuplicateEntryError(Exception):
    pass


class FakeLockError(Exception):
    pass


class FakeDB:
    def __init__(self):
        self.exists_calls = []
        self.set_value_calls = []
        self.sql_calls = []
        self.single_values = {}
        self.korea_calc_reference_run_ids = set()
        self.korea_calc_reference_records = {}
        self.korea_salary_slip_extension_records = {}
        self.korea_severance_slip_records = {}
        self.salary_slip_records = {"SS-0001": {"name": "SS-0001", "employee": "EMP-0001"}}
        self.branch_records = {}
        self.employee_names = {"EMP-0001"}
        self.lock_results = {}
        self.release_results = {}
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
            "Employee": [
                "name",
                "employee_number",
                "employee_name",
                "visa_status_code",
                "kr_employ_ins_exempt",
            ],
            "Branch": [
                "name",
                "company",
                "custom_business_registration_number",
                "custom_worksite_code",
                "custom_worksite_status",
                "custom_effective_from",
                "custom_effective_to",
                "custom_source_modified",
                "custom_sync_status",
                "custom_last_sync_payload",
            ],
        }

    def exists(self, doctype, name):
        self.exists_calls.append((doctype, name))
        if doctype == "Salary Slip":
            if isinstance(name, dict):
                return None
            return name if name in self.salary_slip_records else False
        if doctype == "Employee":
            return name in self.employee_names
        if doctype == "Korea Calc Reference" and isinstance(name, dict):
            return name.get("run_id") in self.korea_calc_reference_run_ids
        if doctype == "Korea Salary Slip Extension":
            if isinstance(name, dict):
                salary_slip = name.get("salary_slip")
                for record_name, record in self.korea_salary_slip_extension_records.items():
                    if record.get("salary_slip") == salary_slip:
                        return record_name
                return None
            return name if name in self.korea_salary_slip_extension_records else None
        if doctype == "Korea Severance Slip":
            if isinstance(name, dict):
                external_run_id = name.get("external_run_id")
                for record_name, record in self.korea_severance_slip_records.items():
                    if record.get("external_run_id") == external_run_id:
                        return record_name
                return None
            return name if name in self.korea_severance_slip_records else None
        if doctype == "Branch":
            return name if name in self.branch_records else None
        return False

    def set_value(self, doctype, name, values, *args, **kwargs):
        self.set_value_calls.append(((doctype, name, values), kwargs))
        if doctype == "Branch":
            record = self.branch_records.setdefault(name, {"name": name})
            if isinstance(values, dict):
                record.update(values)
            else:
                fieldname = values
                value = args[0] if args else kwargs.get("value")
                record[fieldname] = value
        if doctype == "Salary Slip":
            record = self.salary_slip_records.setdefault(name, {"name": name})
            if isinstance(values, dict):
                record.update(values)
            else:
                fieldname = values
                value = args[0] if args else kwargs.get("value")
                record[fieldname] = value
        if doctype == "Korea Salary Slip Extension":
            record = self.korea_salary_slip_extension_records.setdefault(name, {"name": name})
            if isinstance(values, dict):
                record.update(values)
            else:
                fieldname = values
                value = args[0] if args else kwargs.get("value")
                record[fieldname] = value
        if doctype == "Korea Severance Slip":
            record = self.korea_severance_slip_records.setdefault(name, {"name": name})
            if isinstance(values, dict):
                record.update(values)
            else:
                fieldname = values
                value = args[0] if args else kwargs.get("value")
                record[fieldname] = value

    def get_value(self, doctype, name, fieldname=None):
        if doctype == "Branch":
            record = self.branch_records.get(name)
            if not record:
                return None
            if fieldname is None:
                return record
            if isinstance(fieldname, (list, tuple)):
                return {field: record.get(field) for field in fieldname}
            return record.get(fieldname)
        if doctype == "Salary Slip":
            record = self.salary_slip_records.get(name)
            if not record:
                return None
            if fieldname is None:
                return record
            if isinstance(fieldname, (list, tuple)):
                return {field: record.get(field) for field in fieldname}
            return record.get(fieldname)
        if doctype == "Korea Salary Slip Extension":
            record = self.korea_salary_slip_extension_records.get(name)
            if not record:
                return None
            if fieldname is None:
                return record
            if isinstance(fieldname, (list, tuple)):
                return {field: record.get(field) for field in fieldname}
            return record.get(fieldname)
        if doctype == "Korea Severance Slip":
            record = self.korea_severance_slip_records.get(name)
            if not record:
                return None
            if fieldname is None:
                return record
            if isinstance(fieldname, (list, tuple)):
                return {field: record.get(field) for field in fieldname}
            return record.get(fieldname)
        return None

    def get_table_columns(self, doctype):
        return self.table_columns.get(doctype, [])

    def sql(self, query, values=None, as_dict=False):
        self.sql_calls.append({"query": query, "values": values, "as_dict": as_dict})
        if "GET_LOCK" in query:
            lock_name = values[0] if values else None
            return [(self.lock_results.get(lock_name, 1),)]
        if "RELEASE_LOCK" in query:
            lock_name = values[0] if values else None
            return [(self.release_results.get(lock_name, 1),)]
        return []


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
        self.error_logs = []
        self.log_error = lambda *args, **kwargs: self.error_logs.append({"args": args, "kwargs": kwargs})
        self.get_traceback = lambda: "traceback"
        self.local = types.SimpleNamespace(form_dict={}, request=None)
        self.session = types.SimpleNamespace(user="integration@example.com")
        self.LockError = FakeLockError
        self._cache = FakeCache()

    def cache(self):
        return self._cache

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
        if payload.get("doctype") == "Branch":
            branch_name = payload.get("name") or payload.get("branch")

            def insert(ignore_permissions=False):
                record = self.db.branch_records.setdefault(branch_name, {"name": branch_name})
                record.update(payload)
                return record

            return types.SimpleNamespace(insert=insert)

        if payload.get("doctype") == "Korea Calc Reference":
            record_name = payload.get("name") or payload.get("run_id")

            def insert(ignore_permissions=False):
                if payload.get("employee_id") not in self.db.employee_names:
                    raise FakeFrappeError(f"Could not find Employee: {payload.get('employee_id')}")
                if payload.get("run_id") in self.db.korea_calc_reference_run_ids:
                    raise FakeDuplicateEntryError(f"Duplicate run_id: {payload.get('run_id')}")
                record = {"name": record_name}
                record.update(payload)
                self.db.korea_calc_reference_records[record_name] = record
                self.db.korea_calc_reference_run_ids.add(payload.get("run_id"))
                return types.SimpleNamespace(**record)

            return types.SimpleNamespace(insert=insert)

        if payload.get("doctype") == "Korea Salary Slip Extension":
            record_name = payload.get("name") or payload.get("salary_slip")

            def insert(ignore_permissions=False):
                if payload.get("employee") not in self.db.employee_names:
                    raise FakeFrappeError(f"Could not find Employee: {payload.get('employee')}")
                record = {"name": record_name}
                record.update(payload)
                self.db.korea_salary_slip_extension_records[record_name] = record
                return types.SimpleNamespace(**record)

            return types.SimpleNamespace(insert=insert)

        if payload.get("doctype") == "Korea Severance Slip":
            record_name = payload.get("name") or payload.get("external_run_id")

            def insert(ignore_permissions=False):
                if payload.get("employee") not in self.db.employee_names:
                    raise FakeFrappeError(f"Could not find Employee: {payload.get('employee')}")
                record = {"name": record_name}
                record.update(payload)
                self.db.korea_severance_slip_records[record_name] = record
                return types.SimpleNamespace(**record)

            return types.SimpleNamespace(insert=insert)

        self._comments.append(payload)
        return types.SimpleNamespace(insert=lambda ignore_permissions=False: payload)


class FakeCache:
    def __init__(self):
        self.lock_calls = []
        self.lock_enter_calls = []
        self.lock_release_calls = []
        self.lock_unavailable_keys = set()

    def lock(self, key, timeout=None, **kwargs):
        self.lock_calls.append({"key": key, "timeout": timeout, **kwargs})
        return FakeCacheLock(self, key)


class FakeCacheLock:
    def __init__(self, cache, key):
        self.cache = cache
        self.key = key

    def __enter__(self):
        self.cache.lock_enter_calls.append(self.key)
        if self.key in self.cache.lock_unavailable_keys:
            raise FakeLockError(f"Lock unavailable: {self.key}")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.cache.lock_release_calls.append({"key": self.key, "exc_type": exc_type.__name__ if exc_type else None})
        return False


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
                "kr_employ_ins_exempt": 1,
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
        self.assertTrue(result["data"][0]["employment_insurance_exempt"])
        self.assertEqual(result["data"][1]["employment_category"], "foreign_worker")
        self.assertFalse(result["data"][1]["employment_insurance_exempt"])
        self.assertEqual(result["data"][1]["visa_status_code"], "E-9")
        self.assertNotIn("address", result["data"][0])

    def test_export_employee_master_requires_employment_insurance_field(self):
        self.fake_frappe.db.table_columns["Employee"] = [
            "name",
            "employee_number",
            "employee_name",
            "visa_status_code",
        ]

        with self.assertRaises(FakeFrappeError) as exc:
            self.module.export_employee_master(page=1, page_size=1)

        self.assertIn("Employee.kr_employ_ins_exempt custom field is required", str(exc.exception))

    def test_export_employee_master_logs_unknown_employment_type(self):
        self.fake_frappe._employee_rows = [
            {
                "name": "EMP-0099",
                "employee_number": "1099",
                "employee_name": "Park Mystery",
                "company": "Winners",
                "branch": "Seoul",
                "department": "Ops",
                "designation": "Analyst",
                "employment_type": "인턴",
                "date_of_joining": "2026-02-01",
                "relieving_date": None,
                "status": "Active",
                "modified": "2026-04-26 11:00:00",
            }
        ]

        result = self.module.export_employee_master(page=1, page_size=1)

        self.assertEqual(result["data"][0]["employment_type"], "기타")
        self.assertEqual(result["data"][0]["employment_category"], "other")
        self.assertEqual(len(self.fake_frappe.error_logs), 1)
        self.assertIn("Unknown employment_type", self.fake_frappe.error_logs[0]["args"][0])

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

    def test_export_time_and_leave_paginates_full_employee_result_set(self):
        self.fake_frappe._attendance_rows = [
            {
                "name": f"ATT-{index:04d}",
                "employee": f"EMP-{index:04d}",
                "attendance_date": "2026-04-01",
                "status": "Present",
                "shift": "Day",
                "working_hours": 8,
                "modified": "2026-04-01 09:00:00",
            }
            for index in range(1, 251)
        ]

        result = self.module.export_time_and_leave(
            from_date="2026-04-01",
            to_date="2026-04-30",
            page=2,
            page_size=100,
        )

        self.assertEqual(result["meta"], {"page": 2, "page_size": 100, "has_more": True})
        self.assertEqual(len(result["data"]), 100)
        self.assertEqual(result["data"][0]["employee_id"], "EMP-0101")
        self.assertEqual(result["data"][-1]["employee_id"], "EMP-0200")

    def test_export_time_and_leave_company_filter_does_not_truncate_employee_whitelist(self):
        self.fake_frappe._employee_rows = [{"name": f"EMP-{index:04d}"} for index in range(1, 151)]
        self.fake_frappe._attendance_rows = [
            {
                "name": f"ATT-{index:04d}",
                "employee": f"EMP-{index:04d}",
                "attendance_date": "2026-04-01",
                "status": "Present",
                "shift": "Day",
                "working_hours": 8,
                "modified": "2026-04-01 09:00:00",
            }
            for index in range(1, 151)
        ]

        result = self.module.export_time_and_leave(
            from_date="2026-04-01",
            to_date="2026-04-30",
            company="Winners",
            page=2,
            page_size=100,
        )

        self.assertEqual(result["meta"], {"page": 2, "page_size": 100, "has_more": False})
        self.assertEqual(len(result["data"]), 50)
        self.assertEqual(result["data"][0]["employee_id"], "EMP-0101")
        self.assertEqual(result["data"][-1]["employee_id"], "EMP-0150")

    def test_export_time_and_leave_no_data_loss_for_200_employees(self):
        self.fake_frappe._attendance_rows = [
            {
                "name": f"ATT-{index:04d}",
                "employee": f"EMP-{index:04d}",
                "attendance_date": "2026-04-01",
                "status": "Present",
                "shift": "Day",
                "working_hours": 8,
                "modified": "2026-04-01 09:00:00",
            }
            for index in range(1, 201)
        ]

        result = self.module.export_time_and_leave(
            from_date="2026-04-01",
            to_date="2026-04-30",
            page=2,
            page_size=100,
        )

        self.assertEqual(result["meta"], {"page": 2, "page_size": 100, "has_more": False})
        self.assertEqual(len(result["data"]), 100)
        self.assertEqual(result["data"][0]["employee_id"], "EMP-0101")
        self.assertEqual(result["data"][-1]["employee_id"], "EMP-0200")

        attendance_calls = [
            call for call in self.fake_frappe.get_all_calls if call["doctype"] == "Attendance"
        ]
        self.assertEqual(attendance_calls[0]["fields"], ["employee"])
        self.assertIsNotNone(attendance_calls[0]["page_length"])
        self.assertEqual(attendance_calls[-1]["filters"]["employee"][0], "in")
        self.assertEqual(attendance_calls[-1]["filters"]["employee"][1][0], "EMP-0101")
        self.assertEqual(attendance_calls[-1]["filters"]["employee"][1][-1], "EMP-0200")

    def test_export_time_and_leave_no_timeout_for_large_period(self):
        self.fake_frappe._attendance_rows = [
            {
                "name": f"ATT-{index:04d}",
                "employee": f"EMP-{index:04d}",
                "attendance_date": "2026-04-01",
                "status": "Present",
                "shift": "Day",
                "working_hours": 8,
                "modified": "2026-04-01 09:00:00",
            }
            for index in range(1, 601)
        ]
        self.fake_frappe._leave_rows = [
            {
                "name": f"LEAVE-{index:04d}",
                "employee": f"EMP-{index:04d}",
                "leave_type": "연차",
                "from_date": "2026-04-10",
                "to_date": "2026-04-10",
                "half_day": 0,
                "half_day_date": None,
                "total_leave_days": 1,
                "status": "Approved",
                "modified": "2026-04-10 09:00:00",
            }
            for index in range(1, 601)
        ]

        result = self.module.export_time_and_leave(
            from_date="2026-01-01",
            to_date="2026-04-30",
            page=1,
            page_size=100,
        )

        self.assertEqual(result["meta"], {"page": 1, "page_size": 100, "has_more": True})
        self.assertEqual(len(result["data"]), 100)

        stream_calls = [
            call
            for call in self.fake_frappe.get_all_calls
            if call["doctype"] in {"Attendance", "Leave Application"} and call["fields"] == ["employee"]
        ]
        self.assertGreaterEqual(len(stream_calls), 2)
        self.assertTrue(all(call["page_length"] is not None for call in stream_calls))

    def test_apply_worksite_master_from_yaml_creates_branch_record(self):
        result = self.module.apply_worksite_master_from_yaml(
            payload={
                "yaml_version": "2026-04-26",
                "items": [
                    {
                        "company": "Winners",
                        "branch": "Bupyeong",
                        "business_registration_number": "123-45-67890",
                        "worksite_code": "BUP-01",
                        "status": "active",
                        "effective_from": "2026-04-01",
                        "effective_to": None,
                        "source_modified": "2026-04-26 09:00:00",
                    }
                ],
            }
        )

        self.assertEqual(result["yaml_version"], "2026-04-26")
        self.assertEqual(result["applied"], [{"company": "Winners", "branch": "Bupyeong", "action": "created"}])
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(
            self.fake_frappe.db.branch_records["Bupyeong"]["custom_business_registration_number"],
            "123-45-67890",
        )
        self.assertEqual(self.fake_frappe.db.branch_records["Bupyeong"]["custom_sync_status"], "synced")

    def test_apply_worksite_master_from_yaml_updates_existing_branch_and_marks_conflict(self):
        self.fake_frappe.db.branch_records["Bupyeong"] = {
            "name": "Bupyeong",
            "company": "Winners",
            "custom_business_registration_number": "999-99-99999",
            "custom_worksite_code": "OLD",
            "custom_worksite_status": "inactive",
            "custom_effective_from": "2026-03-01",
            "custom_effective_to": None,
            "custom_source_modified": "2026-03-01 09:00:00",
            "custom_sync_status": "manual_override",
        }

        result = self.module.apply_worksite_master_from_yaml(
            payload={
                "yaml_version": "2026-04-26",
                "items": [
                    {
                        "company": "Winners",
                        "branch": "Bupyeong",
                        "business_registration_number": "123-45-67890",
                        "worksite_code": "BUP-01",
                        "status": "active",
                        "effective_from": "2026-04-01",
                        "effective_to": None,
                        "source_modified": "2026-04-26 09:00:00",
                    }
                ],
            }
        )

        self.assertEqual(result["applied"], [{"company": "Winners", "branch": "Bupyeong", "action": "updated"}])
        self.assertEqual(result["conflicts"][0]["resolution"], "yaml_wins")
        self.assertIn("custom_business_registration_number", result["conflicts"][0]["detail"])
        self.assertEqual(
            self.fake_frappe.db.branch_records["Bupyeong"]["custom_business_registration_number"],
            "123-45-67890",
        )
        self.assertEqual(self.fake_frappe.db.branch_records["Bupyeong"]["custom_sync_status"], "conflict_detected")

    def test_apply_worksite_master_from_yaml_ignores_identical_branch_record(self):
        self.fake_frappe.db.branch_records["Bupyeong"] = {
            "name": "Bupyeong",
            "company": "Winners",
            "custom_business_registration_number": "123-45-67890",
            "custom_worksite_code": "BUP-01",
            "custom_worksite_status": "active",
            "custom_effective_from": "2026-04-01",
            "custom_effective_to": None,
            "custom_source_modified": "2026-04-26 09:00:00",
            "custom_sync_status": "synced",
        }

        result = self.module.apply_worksite_master_from_yaml(
            payload={
                "yaml_version": "2026-04-26",
                "items": [
                    {
                        "company": "Winners",
                        "branch": "Bupyeong",
                        "business_registration_number": "123-45-67890",
                        "worksite_code": "BUP-01",
                        "status": "active",
                        "effective_from": "2026-04-01",
                        "effective_to": None,
                        "source_modified": "2026-04-26 09:00:00",
                    }
                ],
            }
        )

        self.assertEqual(result["applied"], [{"company": "Winners", "branch": "Bupyeong", "action": "ignored"}])
        self.assertEqual(result["conflicts"], [])

    def test_apply_worksite_master_from_yaml_handles_branch_without_company_column(self):
        self.fake_frappe.db.table_columns["Branch"] = [
            "name",
            "custom_business_registration_number",
            "custom_worksite_code",
            "custom_worksite_status",
            "custom_effective_from",
            "custom_effective_to",
            "custom_source_modified",
            "custom_sync_status",
            "custom_last_sync_payload",
        ]

        result = self.module.apply_worksite_master_from_yaml(
            payload={
                "yaml_version": "2026-04-26",
                "items": [
                    {
                        "company": "Winners",
                        "branch": "Bupyeong",
                        "business_registration_number": "123-45-67890",
                        "worksite_code": "BUP-01",
                        "status": "active",
                        "effective_from": "2026-04-01",
                        "effective_to": None,
                        "source_modified": "2026-04-26 09:00:00",
                    }
                ],
            }
        )

        self.assertEqual(result["applied"], [{"company": "Winners", "branch": "Bupyeong", "action": "created"}])
        self.assertEqual(self.fake_frappe.db.branch_records["Bupyeong"]["custom_worksite_code"], "BUP-01")
        self.assertNotIn("company", self.fake_frappe.db.branch_records["Bupyeong"])

    def test_apply_worksite_yaml_item_acquires_lock_for_branch(self):
        item = {
            "company": "Winners",
            "branch": "Bupyeong",
            "business_registration_number": "123-45-67890",
            "worksite_code": "BUP-01",
            "status": "active",
            "effective_from": "2026-04-01",
            "effective_to": None,
            "source_modified": "2026-04-26 09:00:00",
        }

        self.module._apply_worksite_yaml_item(item)

        self.assertEqual(
            self.fake_frappe._cache.lock_calls,
            [{"key": "korea-worksite-sync:Bupyeong", "timeout": 10, "blocking_timeout": 0}],
        )
        self.assertEqual(self.fake_frappe._cache.lock_enter_calls, ["korea-worksite-sync:Bupyeong"])

    def test_apply_worksite_yaml_item_releases_lock_after_normal_path(self):
        item = {
            "company": "Winners",
            "branch": "Bupyeong",
            "business_registration_number": "123-45-67890",
            "worksite_code": "BUP-01",
            "status": "active",
            "effective_from": "2026-04-01",
            "effective_to": None,
            "source_modified": "2026-04-26 09:00:00",
        }

        result = self.module._apply_worksite_yaml_item(item)

        self.assertEqual(result, ("created", None))
        self.assertEqual(
            self.fake_frappe._cache.lock_release_calls,
            [{"key": "korea-worksite-sync:Bupyeong", "exc_type": None}],
        )

    def test_apply_worksite_yaml_item_releases_lock_after_throw(self):
        item = {
            "company": "Winners",
            "branch": "Bupyeong",
            "business_registration_number": "123-45-67890",
            "worksite_code": "BUP-01",
            "status": "active",
            "effective_from": "2026-04-01",
            "effective_to": None,
            "source_modified": "2026-04-26 09:00:00",
        }
        original = self.module._persist_branch_worksite_state

        def raising(*args, **kwargs):
            raise FakeFrappeError("boom")

        self.module._persist_branch_worksite_state = raising
        try:
            with self.assertRaises(FakeFrappeError):
                self.module._apply_worksite_yaml_item(item)
        finally:
            self.module._persist_branch_worksite_state = original

        self.assertEqual(
            self.fake_frappe._cache.lock_release_calls,
            [{"key": "korea-worksite-sync:Bupyeong", "exc_type": "FakeFrappeError"}],
        )

    def test_apply_worksite_yaml_item_returns_rejected_when_lock_unavailable(self):
        item = {
            "company": "Winners",
            "branch": "Bupyeong",
            "business_registration_number": "123-45-67890",
            "worksite_code": "BUP-01",
            "status": "active",
            "effective_from": "2026-04-01",
            "effective_to": None,
            "source_modified": "2026-04-26 09:00:00",
        }
        self.fake_frappe._cache.lock_unavailable_keys.add("korea-worksite-sync:Bupyeong")

        result = self.module._apply_worksite_yaml_item(item)

        self.assertEqual(
            result,
            (
                "rejected_locked",
                {
                    "company": "Winners",
                    "branch": "Bupyeong",
                    "reason": "concurrent_sync_in_progress",
                },
            ),
        )
        self.assertEqual(self.fake_frappe._cache.lock_enter_calls, ["korea-worksite-sync:Bupyeong"])
        self.assertEqual(self.fake_frappe._cache.lock_release_calls, [])

    def test_notify_worksite_master_change_returns_auditable_payload(self):
        result = self.module.notify_worksite_master_change(
            payload={
                "event_type": "updated",
                "worksite": {
                    "company": "Winners",
                    "branch": "Bupyeong",
                    "business_registration_number": "123-45-67890",
                    "worksite_code": "BUP-01",
                    "effective_from": "2026-04-01",
                    "status": "active",
                    "modified": "2026-04-26 10:00:00",
                },
            }
        )

        self.assertEqual(result["status"], "received")
        self.assertEqual(result["event_type"], "updated")
        self.assertEqual(result["worksite"]["branch"], "Bupyeong")
        self.assertIn("audit", result)
        self.assertEqual(result["audit"]["resolution_policy"], "yaml_wins")
        self.assertFalse(result["audit"]["queued"])

    def test_notify_worksite_master_change_accepts_json_string_payload(self):
        result = self.module.notify_worksite_master_change(
            payload='{"event_type": "updated", "worksite": {"company": "Winners", "branch": "Bupyeong", "business_registration_number": "123-45-67890", "worksite_code": "BUP-01", "effective_from": "2026-04-01", "status": "active", "modified": "2026-04-26 10:00:00"}}'
        )

        self.assertEqual(result["status"], "received")
        self.assertEqual(result["worksite"]["branch"], "Bupyeong")

    def test_notify_worksite_master_change_ignores_frappe_cmd_kwarg(self):
        result = self.module.notify_worksite_master_change(
            cmd="hrms.api.korea_integration.notify_worksite_master_change",
            event_type="updated",
            worksite={
                "company": "Winners",
                "branch": "Bupyeong",
                "business_registration_number": "123-45-67890",
                "worksite_code": "BUP-01",
                "effective_from": "2026-04-01",
                "status": "active",
                "modified": "2026-04-26 10:00:00",
            },
        )

        self.assertEqual(result["status"], "received")
        self.assertEqual(result["event_type"], "updated")

    def test_apply_worksite_master_from_yaml_ignores_frappe_cmd_kwarg(self):
        result = self.module.apply_worksite_master_from_yaml(
            cmd="hrms.api.korea_integration.apply_worksite_master_from_yaml",
            yaml_version="2026-04-30T00:00:00Z",
            items=[
                {
                    "company": "Winners",
                    "branch": "Bupyeong",
                    "business_registration_number": "123-45-67890",
                    "worksite_code": "BUP-01",
                    "status": "active",
                    "effective_from": "2026-04-01",
                    "effective_to": None,
                    "source_modified": "2026-04-30T00:00:00Z",
                }
            ],
        )

        self.assertEqual(result["applied"][0]["branch"], "Bupyeong")
        self.assertIn(result["applied"][0]["action"], {"created", "updated", "ignored"})

    def test_import_year_end_settlement_result_rejects_unknown_fields(self):
        with self.assertRaises(FakeFrappeError):
            self.module.import_year_end_settlement_result(
                payload={
                    "run_id": "YES-1",
                    "employee_id": "EMP-0001",
                    "settlement_year": 2025,
                    "settlement_kind": "annual_february",
                    "applied_pay_year_month": "2026-02",
                    "prepaid_tax": 100,
                    "determined_tax": 120,
                    "adjustment_tax": 20,
                    "unexpected": "x",
                }
            )

    def test_import_year_end_settlement_result_links_salary_slip_when_external_ref_exists(self):
        result = self.module.import_year_end_settlement_result(
            payload={
                "run_id": "YES-1",
                "employee_id": "EMP-0001",
                "settlement_year": 2025,
                "settlement_kind": "annual_february",
                "applied_pay_year_month": "2026-02",
                "salary_slip_external_ref": "SS-0001",
                "prepaid_tax": 100,
                "determined_tax": 120,
                "adjustment_tax": 20,
                "local_income_tax": 2,
                "note": "final adjustment",
            }
        )

        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["employee_id"], "EMP-0001")
        self.assertEqual(result["settlement_year"], 2025)
        self.assertEqual(result["applied_pay_year_month"], "2026-02")
        self.assertEqual(result["salary_slip"], "SS-0001")
        salary_slip = self.fake_frappe.db.salary_slip_records["SS-0001"]
        self.assertEqual(salary_slip["kr_prepaid_tax"], 100.0)
        self.assertEqual(salary_slip["kr_determined_tax"], 120.0)
        self.assertEqual(salary_slip["kr_adjustment_tax"], 20.0)
        self.assertNotIn("kr_local_income_tax", salary_slip)
        self.assertEqual(salary_slip["kr_year_end_settlement_kind"], "annual_february")
        self.assertEqual(salary_slip["kr_year_end_target_month"], "2026-02")
        self.assertEqual(len(self.fake_frappe._comments), 1)
        self.assertEqual(self.fake_frappe._comments[0]["reference_name"], "SS-0001")
        self.assertIn("year-end settlement", self.fake_frappe._comments[0]["content"])

    def test_import_year_end_settlement_rejects_salary_slip_employee_mismatch(self):
        self.fake_frappe.db.salary_slip_records["SS-0002"] = {"name": "SS-0002", "employee": "EMP-9999"}

        with self.assertRaises(FakeFrappeError):
            self.module.import_year_end_settlement_result(
                payload={
                    "run_id": "YES-MISMATCH-1",
                    "employee_id": "EMP-0001",
                    "settlement_year": 2025,
                    "settlement_kind": "annual_february",
                    "applied_pay_year_month": "2026-02",
                    "salary_slip_external_ref": "SS-0002",
                    "prepaid_tax": 100,
                    "determined_tax": 120,
                    "adjustment_tax": 20,
                }
            )

    def test_import_year_end_settlement_rejects_duplicate_run_id(self):
        self.fake_frappe.db.korea_calc_reference_run_ids.add("YES-1")

        with self.assertRaises(FakeFrappeError):
            self.module.import_year_end_settlement_result(
                payload={
                    "run_id": "YES-1",
                    "employee_id": "EMP-0001",
                    "settlement_year": 2025,
                    "settlement_kind": "annual_february",
                    "applied_pay_year_month": "2026-02",
                    "prepaid_tax": 100,
                    "determined_tax": 120,
                    "adjustment_tax": 20,
                }
            )

        self.assertIn(("Korea Calc Reference", {"run_id": "YES-1"}), self.fake_frappe.db.exists_calls)

    def test_import_severance_result_rejects_pii_fields(self):
        with self.assertRaises(FakeFrappeError):
            self.module.import_severance_result(
                payload={
                    "run_id": "SEV-1",
                    "employee_id": "EMP-0001",
                    "retirement_date": "2026-04-30",
                    "average_wage": 100,
                    "service_years": 3,
                    "severance_pay": 1000,
                    "severance_income_tax": 30,
                    "net_pay": 970,
                    "bank_account_number": "123-456-7890",
                }
            )

    def test_import_severance_result_returns_updated_when_linked_salary_slip_exists(self):
        result = self.module.import_severance_result(
            payload={
                "run_id": "SEV-1",
                "employee_id": "EMP-0001",
                "retirement_date": "2026-04-30",
                "linked_salary_slip": "SS-0001",
                "average_wage": 100,
                "service_years": 3,
                "severance_pay": 1000,
                "severance_income_tax": 30,
                "local_income_tax": 3,
                "net_pay": 967,
                "note": "severance calc",
            }
        )

        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["employee_id"], "EMP-0001")
        self.assertEqual(result["retirement_date"], "2026-04-30")
        self.assertEqual(result["korea_severance_slip"], "SEV-1")
        severance = self.fake_frappe.db.korea_severance_slip_records["SEV-1"]
        self.assertEqual(severance["employee"], "EMP-0001")
        self.assertEqual(severance["linked_salary_slip"], "SS-0001")
        self.assertEqual(severance["average_wage"], 100.0)
        self.assertEqual(severance["service_years"], 3.0)
        self.assertEqual(severance["severance_pay"], 1000.0)
        self.assertEqual(severance["severance_income_tax"], 30.0)
        self.assertEqual(severance["local_income_tax"], 3.0)
        self.assertEqual(severance["net_pay"], 967.0)
        self.assertEqual(severance["linked_calc_reference"], "SEV-1")
        self.assertEqual(len(self.fake_frappe._comments), 1)
        self.assertEqual(self.fake_frappe._comments[0]["reference_name"], "SS-0001")
        self.assertIn("severance import", self.fake_frappe._comments[0]["content"])

    def test_import_severance_result_updates_existing_korea_severance_slip(self):
        self.fake_frappe.db.korea_severance_slip_records["KSEV-0001"] = {
            "name": "KSEV-0001",
            "external_run_id": "SEV-1",
            "employee": "EMP-0001",
            "retirement_date": "2026-03-31",
            "severance_pay": 800.0,
        }

        result = self.module.import_severance_result(
            payload={
                "run_id": "SEV-1",
                "employee_id": "EMP-0001",
                "retirement_date": "2026-04-30",
                "linked_salary_slip": "SS-0001",
                "average_wage": 100,
                "service_years": 3,
                "severance_pay": 1000,
                "severance_income_tax": 30,
                "local_income_tax": 3,
                "net_pay": 967,
            }
        )

        self.assertEqual(result["korea_severance_slip"], "KSEV-0001")
        severance = self.fake_frappe.db.korea_severance_slip_records["KSEV-0001"]
        self.assertEqual(severance["retirement_date"], "2026-04-30")
        self.assertEqual(severance["severance_pay"], 1000.0)
        self.assertIn(
            (("Korea Severance Slip", "KSEV-0001", unittest.mock.ANY), {}),
            self.fake_frappe.db.set_value_calls,
        )

    def test_import_severance_result_rejects_salary_slip_employee_mismatch(self):
        self.fake_frappe.db.salary_slip_records["SS-0002"] = {"name": "SS-0002", "employee": "EMP-9999"}

        with self.assertRaises(FakeFrappeError):
            self.module.import_severance_result(
                payload={
                    "run_id": "SEV-MISMATCH-1",
                    "employee_id": "EMP-0001",
                    "retirement_date": "2026-04-30",
                    "linked_salary_slip": "SS-0002",
                    "average_wage": 100,
                    "service_years": 3,
                    "severance_pay": 1000,
                    "severance_income_tax": 30,
                    "net_pay": 970,
                }
            )

    def test_import_severance_rejects_cross_employee_run_id_reuse(self):
        self.fake_frappe.db.korea_severance_slip_records["KSEV-0001"] = {
            "name": "KSEV-0001",
            "external_run_id": "SEV-1",
            "employee": "EMP-0009",
            "retirement_date": "2026-03-31",
            "severance_pay": 800.0,
        }

        with self.assertRaises(FakeFrappeError) as exc:
            self.module.import_severance_result(
                payload={
                    "run_id": "SEV-1",
                    "employee_id": "EMP-0001",
                    "retirement_date": "2026-04-30",
                    "linked_salary_slip": "SS-0001",
                    "average_wage": 100,
                    "service_years": 3,
                    "severance_pay": 1000,
                    "severance_income_tax": 30,
                    "local_income_tax": 3,
                    "net_pay": 967,
                }
            )

        self.assertIn("already used for employee EMP-0009", str(exc.exception))
        self.assertNotIn(
            (("Korea Severance Slip", "KSEV-0001", unittest.mock.ANY), {}),
            self.fake_frappe.db.set_value_calls,
        )

    def test_import_severance_allows_same_employee_idempotent_update(self):
        self.fake_frappe.db.korea_severance_slip_records["KSEV-0001"] = {
            "name": "KSEV-0001",
            "external_run_id": "SEV-1",
            "employee": "EMP-0001",
            "retirement_date": "2026-03-31",
            "severance_pay": 800.0,
        }

        result = self.module.import_severance_result(
            payload={
                "run_id": "SEV-1",
                "employee_id": "EMP-0001",
                "retirement_date": "2026-04-30",
                "linked_salary_slip": "SS-0001",
                "average_wage": 100,
                "service_years": 3,
                "severance_pay": 1000,
                "severance_income_tax": 30,
                "local_income_tax": 3,
                "net_pay": 967,
            }
        )

        self.assertEqual(result["korea_severance_slip"], "KSEV-0001")
        self.assertIn(
            (("Korea Severance Slip", "KSEV-0001", unittest.mock.ANY), {}),
            self.fake_frappe.db.set_value_calls,
        )

    def test_import_severance_rejects_duplicate_run_id(self):
        self.fake_frappe.db.korea_calc_reference_run_ids.add("SEV-1")

        with self.assertRaises(FakeFrappeError):
            self.module.import_severance_result(
                payload={
                    "run_id": "SEV-1",
                    "employee_id": "EMP-0001",
                    "retirement_date": "2026-04-30",
                    "average_wage": 100,
                    "service_years": 3,
                    "severance_pay": 1000,
                    "severance_income_tax": 30,
                    "net_pay": 970,
                }
            )

        self.assertIn(("Korea Calc Reference", {"run_id": "SEV-1"}), self.fake_frappe.db.exists_calls)

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

    def test_import_payroll_result_rejects_salary_slip_employee_mismatch(self):
        self.fake_frappe.db.salary_slip_records["SS-0002"] = {"name": "SS-0002", "employee": "EMP-9999"}

        with self.assertRaises(FakeFrappeError):
            self.module.import_payroll_result(
                payload={
                    "run_id": "RUN-MISMATCH-1",
                    "employee_id": "EMP-0001",
                    "pay_year_month": "2026-04",
                    "salary_slip_external_ref": "SS-0002",
                    "taxable_items": [{"code": "BASE", "label": "기본급", "amount": 1800}],
                    "non_taxable_items": [],
                    "social_insurance_deductions": {
                        "national_pension": 9,
                        "health_insurance": 18,
                        "long_term_care_insurance": 2.7,
                        "employment_insurance": 3.6,
                    },
                    "withholding_tax": {"income_tax": 27, "local_income_tax": 2.7},
                    "gross_pay": 1800,
                    "total_deduction": 60,
                    "net_pay": 1740,
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

    def test_korea_calc_reference_created_on_import_payroll(self):
        result = self.module.import_payroll_result(
            payload={
                "run_id": "RUN-2",
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
                "engine_version": "engine-1",
                "ruleset_version": "ruleset-1",
            }
        )

        self.assertEqual(result["korea_calc_reference"], "RUN-2")
        record = self.fake_frappe.db.korea_calc_reference_records["RUN-2"]
        self.assertEqual(record["kind"], "payroll")
        self.assertEqual(record["employee_id"], "EMP-0001")
        self.assertEqual(record["pay_year_month"], "2026-04")
        self.assertEqual(record["salary_slip_external_ref"], "SS-0001")
        self.assertEqual(record["imported_by"], "integration@example.com")

    def test_import_payroll_result_creates_korea_salary_slip_extension_when_salary_slip_exists(self):
        result = self.module.import_payroll_result(
            payload={
                "run_id": "RUN-EXT-1",
                "employee_id": "EMP-0001",
                "pay_year_month": "2026-04",
                "salary_slip_external_ref": "SS-0001",
                "taxable_items": [{"code": "BASE", "label": "기본급", "amount": 2000}],
                "non_taxable_items": [{"code": "MEAL", "label": "식대", "amount": 100}],
                "social_insurance_deductions": {
                    "national_pension": 10,
                    "health_insurance": 20,
                    "long_term_care_insurance": 3,
                    "employment_insurance": 4,
                },
                "withholding_tax": {"income_tax": 30, "local_income_tax": 3},
                "gross_pay": 2100,
                "total_deduction": 67,
                "net_pay": 2033,
                "engine_version": "engine-1",
                "ruleset_version": "ruleset-1",
            }
        )

        self.assertEqual(result["korea_salary_slip_extension"], "SS-0001")
        extension = self.fake_frappe.db.korea_salary_slip_extension_records["SS-0001"]
        self.assertEqual(extension["salary_slip"], "SS-0001")
        self.assertEqual(extension["employee"], "EMP-0001")
        self.assertEqual(extension["pay_year_month"], "2026-04")
        self.assertEqual(extension["taxable_total"], 2000)
        self.assertEqual(extension["non_taxable_total"], 100)
        self.assertEqual(extension["national_pension"], 10)
        self.assertEqual(extension["health_insurance"], 20)
        self.assertEqual(extension["long_term_care_insurance"], 3)
        self.assertEqual(extension["employment_insurance"], 4)
        self.assertEqual(extension["income_tax"], 30)
        self.assertEqual(extension["local_income_tax"], 3)
        self.assertEqual(extension["net_pay"], 2033)
        self.assertEqual(extension["engine_version"], "engine-1")
        self.assertEqual(extension["ruleset_version"], "ruleset-1")
        self.assertEqual(extension["linked_calc_reference"], "RUN-EXT-1")

    def test_import_payroll_result_updates_existing_korea_salary_slip_extension(self):
        self.fake_frappe.db.korea_salary_slip_extension_records["KEXT-0001"] = {
            "name": "KEXT-0001",
            "salary_slip": "SS-0001",
            "employee": "EMP-0001",
            "pay_year_month": "2026-03",
            "taxable_total": 1000,
            "linked_calc_reference": "OLD-RUN",
        }

        result = self.module.import_payroll_result(
            payload={
                "run_id": "RUN-EXT-2",
                "employee_id": "EMP-0001",
                "pay_year_month": "2026-04",
                "salary_slip_external_ref": "SS-0001",
                "taxable_items": [{"code": "BASE", "label": "기본급", "amount": 2500}],
                "non_taxable_items": [],
                "social_insurance_deductions": {
                    "national_pension": 11,
                    "health_insurance": 21,
                    "long_term_care_insurance": 4,
                    "employment_insurance": 5,
                },
                "withholding_tax": {"income_tax": 31, "local_income_tax": 3.1},
                "gross_pay": 2500,
                "total_deduction": 71.1,
                "net_pay": 2428.9,
            }
        )

        self.assertEqual(result["korea_salary_slip_extension"], "KEXT-0001")
        extension = self.fake_frappe.db.korea_salary_slip_extension_records["KEXT-0001"]
        self.assertEqual(extension["pay_year_month"], "2026-04")
        self.assertEqual(extension["taxable_total"], 2500)
        self.assertEqual(extension["national_pension"], 11)
        self.assertEqual(extension["linked_calc_reference"], "RUN-EXT-2")
        self.assertIn(
            (("Korea Salary Slip Extension", "KEXT-0001", unittest.mock.ANY), {}),
            self.fake_frappe.db.set_value_calls,
        )

    def test_import_payroll_result_does_not_create_extension_when_salary_slip_external_ref_missing(self):
        result = self.module.import_payroll_result(
            payload={
                "run_id": "RUN-EXT-3",
                "employee_id": "EMP-0001",
                "pay_year_month": "2026-04",
                "salary_slip_external_ref": "SS-4040",
                "taxable_items": [{"code": "BASE", "label": "기본급", "amount": 1800}],
                "non_taxable_items": [],
                "social_insurance_deductions": {
                    "national_pension": 9,
                    "health_insurance": 18,
                    "long_term_care_insurance": 2.7,
                    "employment_insurance": 3.6,
                },
                "withholding_tax": {"income_tax": 27, "local_income_tax": 2.7},
                "gross_pay": 1800,
                "total_deduction": 60,
                "net_pay": 1740,
            }
        )

        self.assertEqual(result["status"], "received")
        self.assertIsNone(result["salary_slip"])
        self.assertIsNone(result["korea_salary_slip_extension"])
        self.assertEqual(self.fake_frappe.db.korea_salary_slip_extension_records, {})

    def test_korea_calc_reference_created_on_import_year_end_settlement(self):
        result = self.module.import_year_end_settlement_result(
            payload={
                "run_id": "YES-2",
                "employee_id": "EMP-0001",
                "settlement_year": 2025,
                "settlement_kind": "annual_february",
                "applied_pay_year_month": "2026-02",
                "salary_slip_external_ref": "SS-0001",
                "prepaid_tax": 100,
                "determined_tax": 120,
                "adjustment_tax": 20,
                "local_income_tax": 2,
                "engine_version": "engine-1",
                "ruleset_version": "ruleset-1",
            }
        )

        self.assertEqual(result["korea_calc_reference"], "YES-2")
        record = self.fake_frappe.db.korea_calc_reference_records["YES-2"]
        self.assertEqual(record["kind"], "year_end_settlement")
        self.assertEqual(record["applied_pay_year_month"], "2026-02")
        self.assertEqual(record["salary_slip_external_ref"], "SS-0001")

    def test_korea_calc_reference_created_on_import_severance(self):
        result = self.module.import_severance_result(
            payload={
                "run_id": "SEV-2",
                "employee_id": "EMP-0001",
                "retirement_date": "2026-04-30",
                "linked_salary_slip": "SS-0001",
                "average_wage": 100,
                "service_years": 3,
                "severance_pay": 1000,
                "severance_income_tax": 30,
                "local_income_tax": 3,
                "net_pay": 967,
                "engine_version": "engine-1",
                "ruleset_version": "ruleset-1",
            }
        )

        self.assertEqual(result["korea_calc_reference"], "SEV-2")
        record = self.fake_frappe.db.korea_calc_reference_records["SEV-2"]
        self.assertEqual(record["kind"], "severance")
        self.assertEqual(record["retirement_date"], "2026-04-30")
        self.assertEqual(record["salary_slip_external_ref"], "SS-0001")

    def test_korea_calc_reference_run_id_unique_constraint(self):
        payload = {
            "run_id": "RUN-UNIQ-1",
            "employee_id": "EMP-0001",
            "kind": "payroll",
            "import_payload": "{}",
            "imported_by": "integration@example.com",
        }

        self.fake_frappe.get_doc({"doctype": "Korea Calc Reference", **payload}).insert(ignore_permissions=True)
        with self.assertRaises(FakeDuplicateEntryError):
            self.fake_frappe.get_doc({"doctype": "Korea Calc Reference", **payload}).insert(ignore_permissions=True)

    def test_korea_calc_reference_employee_id_must_be_existing_employee(self):
        with self.assertRaises(FakeFrappeError):
            self.module.import_payroll_result(
                payload={
                    "run_id": "RUN-MISSING-EMP-1",
                    "employee_id": "EMP-4040",
                    "pay_year_month": "2026-04",
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

    def test_import_payroll_result_acquires_and_releases_run_id_lock(self):
        self.module.import_payroll_result(
            payload={
                "run_id": "RUN-LOCK-1",
                "employee_id": "EMP-0001",
                "pay_year_month": "2026-04",
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

        lock_queries = [call for call in self.fake_frappe.db.sql_calls if "GET_LOCK" in call["query"]]
        release_queries = [call for call in self.fake_frappe.db.sql_calls if "RELEASE_LOCK" in call["query"]]
        self.assertEqual(len(lock_queries), 1)
        self.assertEqual(len(release_queries), 1)
        self.assertEqual(lock_queries[0]["values"][0], "korea_calc_reference:RUN-LOCK-1")
        self.assertEqual(release_queries[0]["values"][0], "korea_calc_reference:RUN-LOCK-1")

    def test_import_payroll_result_rejects_when_run_id_lock_not_acquired(self):
        self.fake_frappe.db.lock_results["korea_calc_reference:RUN-LOCK-FAIL-1"] = 0

        with self.assertRaises(FakeFrappeError):
            self.module.import_payroll_result(
                payload={
                    "run_id": "RUN-LOCK-FAIL-1",
                    "employee_id": "EMP-0001",
                    "pay_year_month": "2026-04",
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

    def test_serialize_import_payload_rejects_pii_again_before_persist(self):
        with self.assertRaises(FakeFrappeError):
            self.module._serialize_import_payload(
                {
                    "run_id": "RUN-PII-1",
                    "employee_id": "EMP-0001",
                    "address": "Seoul",
                }
            )


if __name__ == "__main__":
    unittest.main()
