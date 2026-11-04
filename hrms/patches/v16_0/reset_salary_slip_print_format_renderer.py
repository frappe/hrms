import frappe

PRINT_FORMATS = ("Salary Slip Classic", "Salary Slip Detailed", "Salary Slip Compact")


def execute():
	for print_format in PRINT_FORMATS:
		if frappe.db.get_value("Print Format", print_format, "pdf_generator") == "WeasyPrint":
			frappe.db.set_value(
				"Print Format", print_format, "pdf_generator", "chrome", update_modified=False
			)
