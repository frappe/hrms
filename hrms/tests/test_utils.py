import frappe
from frappe.utils import add_months, get_first_day, get_last_day, getdate, now_datetime

from erpnext.setup.doctype.department.department import get_abbreviated_name
from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.utils import enable_all_roles_and_domains


def before_tests():
	frappe.clear_cache()
	# complete setup if missing
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

	year = now_datetime().year
	if not frappe.get_list("Company"):
		setup_complete(
			{
				"currency": "INR",
				"full_name": "Test User",
				"company_name": "_Test Company",
				"timezone": "Asia/Kolkata",
				"company_abbr": "_TC",
				"industry": "Manufacturing",
				"country": "India",
				"fy_start_date": f"{year}-01-01",
				"fy_end_date": f"{year}-12-31",
				"language": "english",
				"company_tagline": "Testing",
				"email": "test@erpnext.com",
				"password": "test",
				"chart_of_accounts": "Standard",
			}
		)

	enable_all_roles_and_domains()
	set_defaults()
	frappe.db.commit()  # nosemgrep


def set_defaults():
	from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
		create_holiday_list_assignment,
	)
	from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list

	make_holiday_list("Salary Slip Test Holiday List")
	frappe.db.set_value("Company", "_Test Company", "default_holiday_list", "Salary Slip Test Holiday List")
	create_holiday_list_assignment("Company", "_Test Company", "Salary Slip Test Holiday List")


def get_first_sunday(holiday_list="Salary Slip Test Holiday List", for_date=None, find_after_for_date=False):
	date = for_date or getdate()
	month_start_date = get_first_day(date)

	if find_after_for_date:
		# explictly find first sunday after for_date
		# useful when DOJ is after the month start
		month_start_date = date

	month_end_date = get_last_day(date)
	first_sunday = frappe.db.sql(
		"""
		select holiday_date from `tabHoliday`
		where parent = %s
			and holiday_date between %s and %s
		order by holiday_date
	""",
		(holiday_list, month_start_date, month_end_date),
	)[0][0]

	return first_sunday


def get_first_day_for_prev_month():
	prev_month = add_months(getdate(), -1)
	prev_month_first = prev_month.replace(day=1)
	return prev_month_first


def add_date_to_holiday_list(date: str, holiday_list: str, is_half_day: bool = 0) -> None:
	if frappe.db.exists("Holiday", {"parent": holiday_list, "holiday_date": date}):
		return

	holiday_list = frappe.get_doc("Holiday List", holiday_list)
	holiday_list.append(
		"holidays",
		{"holiday_date": date, "description": "test", "is_half_day": is_half_day},
	)
	holiday_list.save()


def create_company(name: str = "_Test Company", is_group: 0 | 1 = 0, parent_company: str | None = None):
	if frappe.db.exists("Company", name):
		return frappe.get_doc("Company", name)

	return frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": name,
			"default_currency": "INR",
			"country": "India",
			"is_group": is_group,
			"parent_company": parent_company,
		}
	).insert()


def create_department(name: str, company: str = "_Test Company") -> str:
	docname = get_abbreviated_name(name, company)

	if frappe.db.exists("Department", docname):
		return docname

	department = frappe.new_doc("Department")
	department.update({"doctype": "Department", "department_name": name, "company": "_Test Company"})
	department.insert()
	return department.name


def create_employee_grade(grade: str, default_structure: str | None = None, default_base: float = 50000):
	if frappe.db.exists("Employee Grade", grade):
		return frappe.get_doc("Employee Grade", grade)
	return frappe.get_doc(
		{
			"doctype": "Employee Grade",
			"__newname": grade,
			"default_salary_structure": default_structure,
			"default_base_pay": default_base,
		}
	).insert()


def create_job_applicant(**args):
	args = frappe._dict(args)
	filters = {
		"applicant_name": args.applicant_name or "_Test Applicant",
		"email_id": args.email_id or "test_applicant@example.com",
	}

	if frappe.db.exists("Job Applicant", filters):
		return frappe.get_doc("Job Applicant", filters)

	job_applicant = frappe.get_doc(
		{
			"doctype": "Job Applicant",
			"status": args.status or "Open",
			"designation": create_designation().name,
		}
	)
	job_applicant.update(filters)
	job_applicant.save()
	return job_applicant


def get_email_by_subject(subject: str) -> str | None:
	return frappe.db.exists("Email Queue", {"message": ("like", f"%{subject}%")})
