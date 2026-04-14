from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	approver_fields = {
		"Employee": [
			{
				"fieldname": "expense_approver",
				"fieldtype": "Link",
				"label": _("Expense Approver"),
				"options": "User",
				"insert_after": "approvers_section",
				"ignore_user_permissions": 1,
			},
			{
				"fieldname": "leave_approver",
				"fieldtype": "Link",
				"label": _("Leave Approver"),
				"options": "User",
				"insert_after": "expense_approver",
				"ignore_user_permissions": 1,
			},
			{
				"fieldname": "shift_request_approver",
				"fieldtype": "Link",
				"label": _("Shift Request Approver"),
				"options": "User",
				"insert_after": "column_break_45",
				"ignore_user_permissions": 1,
			},
		]
	}

	create_custom_fields(approver_fields, ignore_validate=True)
