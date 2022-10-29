# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class LeaveBlockList(Document):
	def validate(self):
		dates = []
		for d in self.get("leave_block_list_dates"):
			# date is not repeated
			if d.block_date in dates:
				frappe.msgprint(_("Date is repeated") + ":" + d.block_date, raise_exception=1)
			dates.append(d.block_date)


@frappe.whitelist()
def get_applicable_block_dates(from_date, to_date, employee=None, company=None, all_lists=False, leave_type=None):
	return frappe.db.get_all("Leave Block List Date", filters={
		"parent": ["IN", get_applicable_block_lists(employee, company, all_lists, leave_type)],
		"block_date": ["BETWEEN", [from_date, to_date]]
	}, fields=['block_date', 'reason'])


def get_applicable_block_lists(employee=None, company=None, all_lists=False, leave_type=None):
	block_lists = []

	if not employee:
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})
		if not employee:
			return []

	if not company:
		company = frappe.db.get_value("Employee", employee, "company")

	def add_block_list(block_list):
		if block_list:
			if all_lists or not is_user_in_allow_list(block_list):
				block_lists.extend(block_list)

	# per department
	department = frappe.db.get_value("Employee", employee, "department")
	if department:
		block_list = frappe.db.get_value("Department", department, "leave_block_list")
		block_list_leave_type = frappe.db.get_value("Leave Block List", block_list, "leave_type")
		if not block_list_leave_type or not leave_type or block_list_leave_type == leave_type:
			add_block_list([block_list])

	# global
	conditions = {
		'applies_to_all_departments': 1,
		'company': company
	}
	if leave_type:
		conditions['leave_type'] = leave_type

	add_block_list(frappe.db.get_all("Leave Block List", filters=conditions, pluck="name"))
	return list(set(block_lists))


def is_user_in_allow_list(block_list):
	return frappe.db.get_value("Leave Block List Allow", {
		"parent": ["IN", block_list],
		"allow_user": frappe.session.user
	}, "allow_user")
