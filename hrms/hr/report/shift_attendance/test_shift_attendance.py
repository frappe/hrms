from datetime import date, datetime, time

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import format_datetime

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type
from hrms.hr.report.shift_attendance.shift_attendance import execute
from hrms.tests.test_utils import create_company


class TestShiftAttendance(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		create_company()
		super().setUpClass()
		frappe.db.delete("Employee", {"company": "_Test Company"})

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
		present_records = report[4][0]["value"]
		self.assertEqual(4, present_records)
		half_day_records = report[4][1]["value"]
		self.assertEqual(1, half_day_records)
		absent_records = report[4][2]["value"]
		self.assertEqual(1, absent_records)
		late_entries = report[4][3]["value"]
		self.assertEqual(2, late_entries)
		early_exits = report[4][4]["value"]
		self.assertEqual(4, early_exits)


def make_checkin(employee, time, log_type):
	frappe.get_doc(
		{
			"doctype": "Employee Checkin",
			"employee": employee,
			"time": time,
			"log_type": log_type,
		}
	).insert()
