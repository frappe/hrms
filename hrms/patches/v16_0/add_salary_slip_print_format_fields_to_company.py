import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	anchor = next(
		(
			fieldname
			for fieldname in ("default_payroll_payable_account", "hr_settings_section")
			if frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": fieldname})
		),
		None,
	)

	create_custom_fields(
		{
			"Company": [
				{
					"fieldname": "salary_slip_print_formats_section",
					"fieldtype": "Section Break",
					"label": _("Salary Slip Print Formats"),
					"insert_after": anchor,
				},
				{
					"fieldname": "standard_salary_slip_print_format",
					"fieldtype": "Link",
					"label": _("Standard Salary Slip Print Format"),
					"options": "Print Format",
					"link_filters": '[["Print Format", "doc_type", "=", "Salary Slip"]]',
					"description": _('Defaults to "Salary Slip Standard" if not set.'),
					"insert_after": "salary_slip_print_formats_section",
				},
				{
					"fieldname": "column_break_salary_slip_print_formats",
					"fieldtype": "Column Break",
					"insert_after": "standard_salary_slip_print_format",
				},
				{
					"fieldname": "timesheet_salary_slip_print_format",
					"fieldtype": "Link",
					"label": _("Timesheet-based Salary Slip Print Format"),
					"options": "Print Format",
					"link_filters": '[["Print Format", "doc_type", "=", "Salary Slip"]]',
					"description": _('Defaults to "Salary Slip based on Timesheet" if not set.'),
					"insert_after": "column_break_salary_slip_print_formats",
				},
			]
		},
		ignore_validate=True,
	)
