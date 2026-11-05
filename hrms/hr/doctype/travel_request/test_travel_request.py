# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.travel_request.travel_request import (
	get_permission_query_conditions,
	has_permission,
)
from hrms.tests.utils import HRMSTestSuite


class TestTravelRequest(HRMSTestSuite):
	def setUp(self):
		if not frappe.db.exists("Purpose of Travel", "_Test Purpose"):
			frappe.get_doc({"doctype": "Purpose of Travel", "purpose_of_travel": "_Test Purpose"}).insert()
		self.employee = make_employee("test_travel_request@example.com", "_Test Company")

	def make_travel_request(self, itinerary=None, costing=None):
		return frappe.get_doc(
			{
				"doctype": "Travel Request",
				"travel_type": "Domestic",
				"purpose_of_travel": "_Test Purpose",
				"employee": self.employee,
				"itinerary": [dict({"travel_from": "A", "travel_to": "B"}, **(itinerary or {}))],
				"costings": [dict({"expense_type": "Travel"}, **(costing or {}))],
			}
		)

	def test_itinerary_dates_are_validated(self):
		request = self.make_travel_request(
			{"departure_date": "2026-10-20 10:00:00", "arrival_date": "2026-10-19 08:00:00"}
		)
		self.assertRaises(frappe.ValidationError, request.insert)

		request = self.make_travel_request(
			{"lodging_required": 1, "check_in_date": "2026-10-25", "check_out_date": "2026-10-21"}
		)
		self.assertRaises(frappe.ValidationError, request.insert)

	def test_costing_total_is_computed(self):
		request = self.make_travel_request(
			costing={"sponsored_amount": 100, "funded_amount": 200, "total_amount": 50}
		).insert()
		self.assertEqual(request.costings[0].total_amount, 300)

	def test_employee_role_limited_to_own_travel_requests(self):
		user = "test_travel_request_self@example.com"
		own_employee = make_employee(user, "_Test Company")
		frappe.get_doc("User", user).add_roles("Employee")
		own_request = self.make_travel_request()
		own_request.employee = own_employee
		other_request = self.make_travel_request()

		self.assertTrue(has_permission(own_request, "write", user))
		self.assertFalse(has_permission(other_request, "read", user))
		self.assertFalse(has_permission(other_request, "create", user))
		self.assertIn(frappe.db.escape(user), get_permission_query_conditions(user))

		self.assertTrue(has_permission(other_request, "read", "Administrator"))
		self.assertEqual(get_permission_query_conditions("Administrator"), "")
