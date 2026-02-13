from datetime import date, datetime, time

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import format_datetime

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type
from hrms.hr.report.shift_attendance.shift_attendance import execute
from hrms.tests.test_utils import create_company


class TestShiftAttendance(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		create_company()
		super().setUpClass()
		frappe.db.delete("Employee", {"company": "_Test Company"})
		frappe.db.delete("Attendance")
		cls.create_records()

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()

	@classmethod
	def create_records(cls):
		cls.shift1 = setup_shift_type(
			shift_type="Shift 1",
			start_time="08:00:00",
			end_time="12:00:00",
			working_hours_threshold_for_half_day=2,
			working_hours_threshold_for_absent=1,
			enable_late_entry_marking=1,
			enable_early_exit_marking=1,
			process_attendance_after="2023-01-01",
			last_sync_of_checkin="2023-01-04 04:00:00",
		)
		cls.shift2 = setup_shift_type(
			shift_type="Shift 2",
			start_time="22:00:00",
			end_time="02:00:00",
			working_hours_threshold_for_half_day=2,
			working_hours_threshold_for_absent=1,
			enable_late_entry_marking=1,
			enable_early_exit_marking=1,
			process_attendance_after="2023-01-01",
			last_sync_of_checkin="2023-01-04 04:00:00",
		)

		cls.emp1 = make_employee(
			"employee1@example.com",
			company="_Test Company",
			default_shift="Shift 1",
		)
		cls.emp2 = make_employee(
			"employee2@example.com",
			company="_Test Company",
			default_shift="Shift 2",
		)

		# Present | Early Entry | Late Exit
		make_checkin(cls.emp1, datetime(2023, 1, 1, 7, 30), "IN")
		make_checkin(cls.emp1, datetime(2023, 1, 1, 12, 30), "OUT")
		# Present | Late Entry | Late Exit
		make_checkin(cls.emp1, datetime(2023, 1, 2, 8, 30), "IN")
		make_checkin(cls.emp1, datetime(2023, 1, 2, 12, 30), "OUT")
		# Present | Early Entry | Early Exit
		make_checkin(cls.emp1, datetime(2023, 1, 3, 7, 30), "IN")
		make_checkin(cls.emp1, datetime(2023, 1, 3, 11, 30), "OUT")
		# Present | Late Entry | Early Exit
		make_checkin(cls.emp2, datetime(2023, 1, 1, 22, 30), "IN")
		make_checkin(cls.emp2, datetime(2023, 1, 2, 1, 30), "OUT")
		# Half Day | Early Entry | Early Exit
		make_checkin(cls.emp2, datetime(2023, 1, 2, 21, 30), "IN")
		make_checkin(cls.emp2, datetime(2023, 1, 2, 23, 15), "OUT")
		# Absent | Early Entry | Early Exit
		make_checkin(cls.emp2, datetime(2023, 1, 3, 21, 30), "IN")
		make_checkin(cls.emp2, datetime(2023, 1, 3, 22, 15), "OUT")

		cls.shift1.process_auto_attendance()
		cls.shift2.process_auto_attendance()

	def test_data(self):
		filters = frappe._dict(
			{
				"company": "_Test Company",
				"from_date": date(2023, 1, 1),
				"to_date": date(2023, 1, 3),
			}
		)
		report = execute(filters)
		data = report[1]
		for i, d in enumerate(data):
			data[i] = {k: d[k] for k in ("shift", "attendance_date", "status", "in_time", "out_time")}
		expected_data = [
			{
				"shift": "Shift 1",
				"attendance_date": date(2023, 1, 1),
				"status": "Present",
				"in_time": time(7, 30),
				"out_time": time(12, 30),
			},
			{
				"shift": "Shift 1",
				"attendance_date": date(2023, 1, 2),
				"status": "Present",
				"in_time": time(8, 30),
				"out_time": time(12, 30),
			},
			{
				"shift": "Shift 1",
				"attendance_date": date(2023, 1, 3),
				"status": "Present",
				"in_time": time(7, 30),
				"out_time": time(11, 30),
			},
			{
				"shift": "Shift 2",
				"attendance_date": date(2023, 1, 1),
				"status": "Present",
				"in_time": format_datetime(datetime(2023, 1, 1, 22, 30)),
				"out_time": format_datetime(datetime(2023, 1, 2, 1, 30)),
			},
			{
				"shift": "Shift 2",
				"attendance_date": date(2023, 1, 2),
				"status": "Half Day",
				"in_time": time(21, 30),
				"out_time": time(23, 15),
			},
			{
				"shift": "Shift 2",
				"attendance_date": date(2023, 1, 3),
				"status": "Absent",
				"in_time": time(21, 30),
				"out_time": time(22, 15),
			},
		]
		self.assertEqual(expected_data, data)

	def test_chart(self):
		filters = frappe._dict(
			{
				"company": "_Test Company",
				"from_date": date(2023, 1, 1),
				"to_date": date(2023, 1, 3),
			}
		)
		report = execute(filters)
		chart_data = report[3]["data"]
		expected_labels = ["Shift 1", "Shift 2"]
		self.assertEqual(expected_labels, chart_data["labels"])
		expected_values = [3, 3]
		self.assertEqual(expected_values, chart_data["datasets"][0]["values"])

	def test_report_summary(self):
		filters = frappe._dict(
			{
				"company": "_Test Company",
				"from_date": date(2023, 1, 1),
				"to_date": date(2023, 1, 3),
			}
		)
		report = execute(filters)
		chart_data = get_chart_data(report)

		self.assertEqual(4, chart_data.present_records)
		self.assertEqual(1, chart_data.half_day_records)
		self.assertEqual(1, chart_data.absent_records)
		self.assertEqual(2, chart_data.late_entries)
		self.assertEqual(4, chart_data.early_exits)

	def test_user_permission_on_attendance_records(self):
		manager = frappe.get_doc("Employee", {"user_id": "employee1@example.com"})
		assistant = frappe.get_doc("Employee", {"user_id": "employee2@example.com"})

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"from_date": date(2023, 1, 1),
				"to_date": date(2023, 1, 3),
			}
		)

		frappe.set_user("employee1@example.com")  # only see their own records
		report = execute(filters)
		chart_data = get_chart_data(report)
		self.assertEqual(3, chart_data.total_records)
		self.assertEqual(3, chart_data.present_records)
		self.assertEqual(0, chart_data.half_day_records)
		self.assertEqual(0, chart_data.absent_records)
		self.assertEqual(1, chart_data.late_entries)
		self.assertEqual(1, chart_data.early_exits)

		frappe.set_user("employee2@example.com")  # only see their own records
		report = execute(filters)
		chart_data = get_chart_data(report)

		self.assertEqual(3, chart_data.total_records)
		self.assertEqual(1, chart_data.present_records)
		self.assertEqual(1, chart_data.half_day_records)
		self.assertEqual(1, chart_data.absent_records)
		self.assertEqual(1, chart_data.late_entries)
		self.assertEqual(3, chart_data.early_exits)

		frappe.set_user("Administrator")
		assistant.reports_to = manager.name
		assistant.save()

		frappe.set_user("employee1@example.com")  # see their own and their reporter's records
		report = execute(filters)
		chart_data = get_chart_data(report)

		self.assertEqual(6, chart_data.total_records)
		self.assertEqual(4, chart_data.present_records)
		self.assertEqual(1, chart_data.half_day_records)
		self.assertEqual(1, chart_data.absent_records)
		self.assertEqual(2, chart_data.late_entries)
		self.assertEqual(4, chart_data.early_exits)

		frappe.set_user("Administrator")
		assistant.reports_to = ""
		assistant.save()

	def test_get_attendance_records_without_checkins(self):
		emp = make_employee("test_shift_report@example.com", company="_Test Company")

		mark_attendance(emp, date(2023, 1, 1), "Present", "Shift 1", late_entry=1, early_exit=0)
		mark_attendance(emp, date(2023, 1, 2), "Half Day", "Shift 2", late_entry=0, early_exit=1)
		mark_attendance(emp, date(2023, 1, 2), "Absent", "Shift 1", late_entry=1, early_exit=1)

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"from_date": date(2023, 1, 1),
				"to_date": date(2023, 1, 3),
				"include_attendance_without_checkins": 1,
			}
		)

		report = execute(filters)
		table_data = report[1]
		self.assertEqual(len(table_data), 9)

		chart_data = get_chart_data(report)
		self.assertEqual(chart_data.present_records, 5)
		self.assertEqual(chart_data.half_day_records, 2)
		self.assertEqual(chart_data.absent_records, 2)
		self.assertEqual(chart_data.late_entries, 4)
		self.assertEqual(chart_data.early_exits, 6)

		# filter by shift
		filters["shift"] = "Shift 1"
		report = execute(filters)
		table_data = report[1]
		self.assertEqual(len(table_data), 5)

		chart_data = get_chart_data(report)

		self.assertEqual(chart_data.present_records, 4)
		self.assertEqual(chart_data.half_day_records, 0)
		self.assertEqual(chart_data.absent_records, 1)
		self.assertEqual(chart_data.late_entries, 3)
		self.assertEqual(chart_data.early_exits, 2)


def get_chart_data(report):
	return frappe._dict(
		total_records=len(report[1]),
		present_records=report[4][0]["value"],
		half_day_records=report[4][1]["value"],
		absent_records=report[4][2]["value"],
		late_entries=report[4][3]["value"],
		early_exits=report[4][4]["value"],
	)


def make_checkin(employee, time, log_type):
	frappe.get_doc(
		{
			"doctype": "Employee Checkin",
			"employee": employee,
			"time": time,
			"log_type": log_type,
		}
	).insert()
