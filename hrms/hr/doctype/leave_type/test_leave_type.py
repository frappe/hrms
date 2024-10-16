# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

test_records = frappe.get_test_records("Leave Type")


def create_leave_type(**args):
	args = frappe._dict(args)
	if frappe.db.exists("Leave Type", args.leave_type_name):
		frappe.delete_doc("Leave Type", args.leave_type_name, force=True)

	leave_type = frappe.get_doc(
		{
			"doctype": "Leave Type",
			"leave_type_name": args.leave_type_name or "_Test Leave Type",
			"include_holiday": args.include_holidays or 1,
			"allow_encashment": args.allow_encashment or 0,
			"is_earned_leave": args.is_earned_leave or 0,
			"is_lwp": args.is_lwp or 0,
			"is_ppl": args.is_ppl or 0,
			"is_carry_forward": args.is_carry_forward or 0,
			"expire_carry_forwarded_leaves_after_days": args.expire_carry_forwarded_leaves_after_days or 0,
			"non_encashable_leaves": args.non_encashable_leaves or 5,
			"earning_component": "Leave Encashment",
			"max_leaves_allowed": args.max_leaves_allowed,
			"maximum_carry_forwarded_leaves": args.maximum_carry_forwarded_leaves,
		}
	)

	if leave_type.is_ppl:
		leave_type.fraction_of_daily_salary_per_leave = args.fraction_of_daily_salary_per_leave or 0.5

	leave_type.insert()

	return leave_type
