# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from datetime import datetime

import frappe
from frappe.utils import add_days, get_time, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_checkin.employee_checkin import CheckinRadiusExceededError
from hrms.hr.doctype.employee_checkin.test_employee_checkin import make_checkin, make_shift_location
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.tests.utils import HRMSTestSuite


class TestShiftLocation(HRMSTestSuite):
	def test_checkin_radius_requires_coordinates(self):
		location = frappe.get_doc(
			{"doctype": "Shift Location", "location_name": "No Coordinates", "checkin_radius": 200}
		)
		self.assertRaises(frappe.ValidationError, location.insert)

		location.checkin_radius = 0
		location.insert()

	@HRMSTestSuite.change_settings("HR Settings", {"allow_geolocation_tracking": 1})
	def test_geofencing_for_overnight_shift_after_assignment_end_date(self):
		employee = make_employee("test_geofence_night@example.com", company="_Test Company")
		shift = setup_shift_type(shift_type="Geofence Night", start_time="22:00:00", end_time="06:00:00")
		location = make_shift_location("Geofence Night Loc", 24, 72)
		date = add_days(getdate(), -2)
		make_shift_assignment(shift.name, employee, date, date, shift_location=location.name)

		# check-out on the morning after the assignment's last night still belongs to that shift
		log = frappe.get_doc(
			{
				"doctype": "Employee Checkin",
				"employee": employee,
				"time": datetime.combine(add_days(date, 1), get_time("06:05:00")),
				"log_type": "OUT",
				"latitude": 20,
				"longitude": 65,
			}
		)
		self.assertRaises(CheckinRadiusExceededError, log.insert)

		make_checkin(
			employee, datetime.combine(add_days(date, 1), get_time("06:10:00")), 24.001, 72.001, "OUT"
		)
