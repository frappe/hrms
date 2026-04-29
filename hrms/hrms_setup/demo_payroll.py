import frappe
from frappe.utils import add_days, getdate


def setup_payroll_runs():
	DEMO_COMPANY = "Sparrow Tech Pvt Ltd"

	company = frappe.db.exists("Company", DEMO_COMPANY)
	if not company:
		first_company = frappe.get_all("Company", pluck="name")
		if not first_company:
			frappe.publish_realtime("demo_progress", {"message": "No companies found, skipping payroll"})
			return
		company = first_company[0]
	else:
		company = DEMO_COMPANY

	currencies = frappe.get_all(
		"Salary Structure",
		filters={"company": company, "docstatus": 1, "is_active": "Yes"},
		pluck="currency",
		distinct=True,
	)

	if not currencies:
		frappe.publish_realtime("demo_progress", {"message": "No Salary Structures found, skipping payroll"})
		return

	current_date = getdate()
	months = []

	for i in range(1, 3):
		month_end = add_days(current_date, -i * 30)
		month_start = getdate(f"{month_end.year}-{month_end.month:02d}-01")
		month_end_date = add_days(add_days(month_start, 31), -1)
		months.append({"start": month_start, "end": min(month_end_date, add_days(current_date, -1))})

	months.reverse()

	created = 0
	for month in months:
		for currency in currencies:
			try:
				payroll_payable_account = get_payroll_payable_account(company, currency)
				if not payroll_payable_account:
					continue

				payment_account = get_default_payment_account(company)

				payroll_entry = frappe.get_doc(
					{
						"doctype": "Payroll Entry",
						"company": company,
						"payroll_frequency": "Monthly",
						"currency": currency,
						"start_date": month["start"],
						"end_date": month["end"],
						"posting_date": month["end"],
						"payment_account": payment_account,
						"payroll_payable_account": payroll_payable_account,
						"exchange_rate": 1,
					}
				)

				payroll_entry.insert(ignore_permissions=True)

				payroll_entry.fill_employee_details()

				payroll_entry.create_salary_slips()

				payroll_entry.reload()

				for emp in payroll_entry.employees:
					salary_slips = frappe.get_all(
						"Salary Slip",
						filters={
							"employee": emp.employee,
							"payroll_entry": payroll_entry.name,
							"docstatus": 0,
						},
						pluck="name",
					)
					for ss_name in salary_slips:
						frappe.get_doc("Salary Slip", ss_name).submit()

				payroll_entry.submit()
				created += 1

			except Exception as e:
				frappe.log_error(f"Failed to create payroll for {month['start']} currency {currency}", str(e))
				continue

	frappe.publish_realtime("demo_progress", {"message": f"Created {created} Payroll Entries"})


def get_default_payment_account(company):
	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "account_type": "Bank", "is_group": 0},
		pluck="name",
		limit=1,
	)
	if accounts:
		return accounts[0]

	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "is_group": 0},
		pluck="name",
		limit=5,
	)
	for acc in accounts:
		if "bank" in acc.lower() or "cash" in acc.lower():
			return acc
	return accounts[0] if accounts else None


def get_payroll_payable_account(company, currency):
	ssa_list = frappe.get_all(
		"Salary Structure Assignment",
		filters={"company": company, "docstatus": 1},
		fields=["payroll_payable_account"],
		distinct=True,
	)

	for ssa in ssa_list:
		if ssa.payroll_payable_account:
			return ssa.payroll_payable_account

	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "account_type": "Payable", "is_group": 0},
		pluck="name",
		limit=5,
	)
	for acc in accounts:
		if "payable" in acc.lower() or "salary" in acc.lower() or "wages" in acc.lower():
			return acc
	return accounts[0] if accounts else None
