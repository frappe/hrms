from datetime import datetime

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, get_time, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.shift_type.test_shift_type import setup_shift_type
from hrms.hr.report.shift_attendance.shift_attendance import execute
from hrms.tests.test_utils import create_company


class TestShiftAttendance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		create_company()
		super().setUpClass()
		frappe.db.sql("delete from `tabEmployee` where company='_Test Company'")

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
			enable_entry_grace_period=1,
			enable_exit_grace_period=1,
		)
		cls.shift2 = setup_shift_type(
			shift_type="Shift 2",
			start_time="22:00:00",
			end_time="02:00:00",
			working_hours_threshold_for_half_day=2,
			working_hours_threshold_for_absent=1,
			enable_entry_grace_period=1,
			enable_exit_grace_period=1,
		)

		cls.emp1 = make_employee(
			"employee1@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-10-2021"),
			default_shift="Shift 1",
		)
		cls.emp2 = make_employee(
			"employee2@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-12-2021"),
			default_shift="Shift 2",
		)

		# Present | Early Entry | Late Exit
		make_checkin(cls.emp1, get_timestamp("07:30:00", 2), "IN")
		make_checkin(cls.emp1, get_timestamp("12:30:00", 2), "OUT")
		# Present | Late Entry | Late Exit
		make_checkin(cls.emp1, get_timestamp("08:30:00", 1), "IN")
		make_checkin(cls.emp1, get_timestamp("12:30:00", 1), "OUT")
		# Present | Early Entry | Early Exit
		make_checkin(cls.emp1, get_timestamp("07:30:00", 0), "IN")
		make_checkin(cls.emp1, get_timestamp("11:30:00", 0), "OUT")
		# Present | Late Entry | Early Exit
		make_checkin(cls.emp2, get_timestamp("22:30:00", 2), "IN")
		make_checkin(cls.emp2, get_timestamp("01:30:00", 1), "OUT")
		# Half Day | Early Entry | Early Exit
		make_checkin(cls.emp2, get_timestamp("21:30:00", 1), "IN")
		make_checkin(cls.emp2, get_timestamp("23:15:00", 1), "OUT")
		# Absent | Early Entry | Early Exit
		make_checkin(cls.emp2, get_timestamp("21:30:00", 0), "IN")
		make_checkin(cls.emp2, get_timestamp("22:15:00", 0), "OUT")

		cls.shift1.process_auto_attendance()
		cls.shift2.process_auto_attendance()

	def test_data(self):
		import datetime

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"from_date": add_days(getdate(), -2),
				"to_date": getdate(),
			}
		)
		report = execute(filters)
		data = report[1]
		for i, d in enumerate(data):
			data[i] = {
				k: d[k] for k in ("employee", "shift", "attendance_date", "status", "in_time", "out_time")
			}
		expected_data = [
			{
				"employee": "EMP-00001",
				"shift": "Shift 1",
				"attendance_date": add_days(getdate(), -2),
				"status": "Present",
				"in_time": datetime.time(7, 30),
				"out_time": datetime.time(12, 30),
			},
			{
				"employee": "EMP-00001",
				"shift": "Shift 1",
				"attendance_date": add_days(getdate(), -1),
				"status": "Present",
				"in_time": datetime.time(8, 30),
				"out_time": datetime.time(12, 30),
			},
			{
				"employee": "EMP-00001",
				"shift": "Shift 1",
				"attendance_date": getdate(),
				"status": "Present",
				"in_time": datetime.time(7, 30),
				"out_time": datetime.time(11, 30),
			},
			{
				"employee": "EMP-00002",
				"shift": "Shift 2",
				"attendance_date": add_days(getdate(), -2),
				"status": "Present",
				"in_time": get_timestamp("22:30:00", 2),
				"out_time": get_timestamp("01:30:00", 1),
			},
			{
				"employee": "EMP-00002",
				"shift": "Shift 2",
				"attendance_date": add_days(getdate(), -1),
				"status": "Half Day",
				"in_time": datetime.time(21, 30),
				"out_time": datetime.time(23, 15),
			},
			{
				"employee": "EMP-00002",
				"shift": "Shift 2",
				"attendance_date": getdate(),
				"status": "Absent",
				"in_time": datetime.time(21, 30),
				"out_time": datetime.time(22, 15),
			},
		]
		self.assertEqual(expected_data, data)

	def test_chart(self):
		filters = frappe._dict(
			{
				"company": "_Test Company",
				"from_date": add_days(getdate(), -2),
				"to_date": getdate(),
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
				"from_date": add_days(getdate(), -2),
				"to_date": getdate(),
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
	log = frappe.get_doc(
		{
			"doctype": "Employee Checkin",
			"employee": employee,
			"time": time,
			"log_type": log_type,
		}
	).insert()


# Returns timespamp after attaching 'time' to 'days_before' days before today
def get_timestamp(time, days_before):
	today = getdate()
	timestamp = datetime.combine(today, get_time(time))
	return add_days(timestamp, -days_before)
