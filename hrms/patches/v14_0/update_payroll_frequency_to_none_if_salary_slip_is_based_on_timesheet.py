import frappe


def execute():
	frappe.reload_doc("payroll", "doctype", "salary_structure")

	salary_strucutres = frappe.get_all(
		"Salary Structure", filters={"salary_slip_based_on_timesheet": 1}, fields=["name"]
	)

	if len(salary_strucutres) > 0:
		for salary_strucutre in salary_strucutres:
			frappe.db.set_value("Salary Structure", salary_strucutre.name, "payroll_frequency", "")
