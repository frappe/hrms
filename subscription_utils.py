import frappe


@frappe.whitelist(allow_guest=True)
def get_add_on_details(site_details: dict) -> dict[str, int]:
	"""
	Returns the number of employees to be billed under add-ons for SAAS subscription
	site_details = {
	        "country": "India",
	        "plan": "Basic",
	        "credit_balance": 1000,
	        "add_ons": {
	                "employee": 2,
	        },
	        "expiry_date": "2021-01-01", # as per current usage
	}
	"""
	EMPLOYEE_LIMITS = {"Basic": 25, "Essential": 50, "Professional": 100}
	add_on_details = {}

	employees_included_in_plan = EMPLOYEE_LIMITS.get(site_details.get("plan"))
	if employees_included_in_plan:
		active_employees = get_active_employees()
		add_on_employees = active_employees - employees_included_in_plan
	else:
		add_on_employees = 0

	add_on_details["employees"] = add_on_employees
	return add_on_details


def get_active_employees() -> int:
	return frappe.db.count("Employee", {"status": "Active"})
