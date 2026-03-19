# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

import erpnext

from hrms.tests.utils import HRMSTestSuite


def create_leave_period(from_date, to_date, company=None):
	leave_period = frappe.db.get_value(
		"Leave Period",
		dict(
			company=company or "_Test Company",
			from_date=from_date,
			to_date=to_date,
			is_active=1,
		),
		"name",
	)
	if leave_period:
		return frappe.get_doc("Leave Period", leave_period)

	leave_period = frappe.get_doc(
		{
			"doctype": "Leave Period",
			"company": company or "_Test Company",
			"from_date": from_date,
			"to_date": to_date,
			"is_active": 1,
		}
	).insert()
	return leave_period
