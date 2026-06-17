import frappe


def setup_payroll_runs():
	from hrms.hrms_setup.demo import get_demo_records

	frappe.db.set_single_value("Payroll Settings", "email_salary_slip_to_employee", 0)

	records = get_demo_records("payroll_entry")
	clear_stale_draft_payroll_entries(records)

	for record in records:
		if not frappe.db.exists("Company", record.get("company")):
			continue

		try:
			existing_payroll_entry = get_existing_payroll_entry(record)
			if existing_payroll_entry:
				complete_payroll_entry(existing_payroll_entry)
				continue

			payroll_entry = frappe.get_doc(record)
			payroll_entry.insert(ignore_permissions=True)
			frappe.db.commit()

			complete_payroll_entry(payroll_entry.name)
		except Exception as e:
			frappe.log_error(
				f"Failed to create payroll for {record.get('start_date')} {record.get('currency')}", str(e)
			)
			continue


def clear_stale_draft_payroll_entries(records):
	expected = {
		(record.get("company"), record.get("currency"), record.get("start_date"), record.get("end_date"))
		for record in records
	}
	companies = [company for company in {record[0] for record in expected} if company]
	if not companies:
		return

	for payroll_entry in frappe.get_all(
		"Payroll Entry",
		filters={"company": ["in", companies], "docstatus": 0},
		fields=["name", "company", "currency", "start_date", "end_date"],
	):
		key = (
			payroll_entry.company,
			payroll_entry.currency,
			str(payroll_entry.start_date),
			str(payroll_entry.end_date),
		)
		if key in expected:
			continue

		if frappe.db.exists("Salary Slip", {"payroll_entry": payroll_entry.name, "docstatus": ("!=", 2)}):
			continue

		frappe.delete_doc("Payroll Entry", payroll_entry.name, ignore_permissions=True, force=True)

	frappe.db.commit()


def get_existing_payroll_entry(record):
	return frappe.db.exists(
		"Payroll Entry",
		{
			"company": record.get("company"),
			"currency": record.get("currency"),
			"start_date": record.get("start_date"),
			"end_date": record.get("end_date"),
			"docstatus": ("!=", 2),
		},
	)


def complete_payroll_entry(payroll_entry_name):
	payroll_entry = frappe.get_doc("Payroll Entry", payroll_entry_name)

	if payroll_entry.docstatus == 0:
		if not payroll_entry.employees:
			payroll_entry.fill_employee_details()
			payroll_entry.save(ignore_permissions=True)
			frappe.db.commit()
			payroll_entry.reload()

		if not payroll_entry.employees:
			frappe.delete_doc("Payroll Entry", payroll_entry.name, ignore_permissions=True, force=True)
			frappe.db.commit()
			return

		payroll_entry.submit()
		frappe.db.commit()

	submit_salary_slips(payroll_entry.name)


def submit_salary_slips(payroll_entry_name):
	payroll_entry = frappe.get_doc("Payroll Entry", payroll_entry_name)
	if payroll_entry.docstatus != 1 or payroll_entry.salary_slips_submitted:
		return

	payroll_entry.submit_salary_slips()
	payroll_entry.reload()

	submitted_salary_slips = payroll_entry.get_sal_slip_list(ss_status=1)
	if submitted_salary_slips and not payroll_entry.salary_slips_submitted:
		submitted = [frappe.get_doc("Salary Slip", entry[0]) for entry in submitted_salary_slips]
		payroll_entry.make_accrual_jv_entry(submitted)
		payroll_entry.email_salary_slip(submitted)
		payroll_entry.db_set({"salary_slips_submitted": 1, "status": "Submitted", "error_message": ""})

	frappe.db.commit()
