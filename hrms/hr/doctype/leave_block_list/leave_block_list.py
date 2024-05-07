# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class LeaveBlockList(Document):
	def validate(self):
		dates = []
		for d in self.get("leave_block_list_dates"):
			# date is not repeated
			if d.block_date in dates:
				frappe.msgprint(_("Date is repeated") + ":" + d.block_date, raise_exception=1)
			dates.append(d.block_date)

	@frappe.whitelist()
	def set_weekly_off_dates(self, start_date, end_date, days, reason):
		date_list = self.get_block_dates_from_date(start_date, end_date, days)
		for date in date_list:
			self.append("leave_block_list_dates", {"block_date": date, "reason": reason})

	def get_block_dates_from_date(self, start_date, end_date, days):
		start_date, end_date = getdate(start_date), getdate(end_date)

		import calendar
		from datetime import timedelta

		date_list = []
		existing_date_list = [getdate(d.block_date) for d in self.get("leave_block_list_dates")]

		while start_date <= end_date:
			if start_date not in existing_date_list and calendar.day_name[start_date.weekday()] in days:
				date_list.append(start_date)
			start_date += timedelta(days=1)

		return date_list


@frappe.whitelist()
def get_applicable_block_dates(
	from_date, to_date, employee=None, company=None, all_lists=False, leave_type=None
):
	return frappe.db.get_all(
		"Leave Block List Date",
		filters={
			"parent": ["IN", get_applicable_block_lists(employee, company, all_lists, leave_type)],
			"block_date": ["BETWEEN", [from_date, to_date]],
		},
		fields=["block_date", "reason"],
	)


def get_applicable_block_lists(employee=None, company=None, all_lists=False, leave_type=None):
	block_lists = []

	if not employee:
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})
		if not employee:
			return []

	if not company:
		company = frappe.db.get_value("Employee", employee, "company")

	def add_block_list(block_list):
		for d in block_list:
			if all_lists or not is_user_in_allow_list(d):
				block_lists.append(d)

	# per department
	department = frappe.db.get_value("Employee", employee, "department")
	if department:
		block_list = frappe.db.get_value("Department", department, "leave_block_list")
		block_list_leave_type = frappe.db.get_value("Leave Block List", block_list, "leave_type")
		if not block_list_leave_type or not leave_type or block_list_leave_type == leave_type:
			add_block_list([block_list])

	# global
	conditions = {"applies_to_all_departments": 1, "company": company}
	if leave_type:
		conditions["leave_type"] = ["IN", (leave_type, "", None)]

	add_block_list(frappe.db.get_all("Leave Block List", filters=conditions, pluck="name"))
	return list(set(block_lists))


def is_user_in_allow_list(block_list):
	return frappe.db.get_value(
		"Leave Block List Allow",
		{"parent": block_list, "allow_user": frappe.session.user},
		"allow_user",
	)
