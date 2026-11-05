import math

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, formatdate, get_last_day, get_link_to_form, getdate

from hrms.hr.utils import get_salary_assignments
from hrms.payroll.doctype.salary_structure.salary_structure import _make_salary_slip


def calculate_annual_eligible_hra_exemption(doc):
	basic_component, hra_component = frappe.db.get_value(
		"Company", doc.company, ["basic_component", "hra_component"]
	)

	if not (basic_component and hra_component):
		frappe.throw(
			_("Please set Basic and HRA component in Company {0}").format(
				get_link_to_form("Company", doc.company)
			)
		)

	annual_exemption = monthly_exemption = hra_amount = basic_amount = months = 0

	if hra_component and basic_component:
		assignments = get_salary_assignments(doc.employee, doc.payroll_period)

		if not assignments and doc.docstatus == 1:
			frappe.throw(_("Salary Structure must be submitted before submission of {0}").format(doc.doctype))

		period_start_date = frappe.db.get_value("Payroll Period", doc.payroll_period, "start_date")

		assignment_dates = []
		for assignment in assignments:
			# if assignment is before payroll period, use period start date to get the correct days
			assignment.from_date = max(assignment.from_date, period_start_date)
			assignment_dates.append(assignment.from_date)

		for idx, assignment in enumerate(assignments):
			if has_hra_component(assignment.salary_structure, hra_component):
				frequency = frappe.get_value(
					"Salary Structure", assignment.salary_structure, "payroll_frequency"
				)
				basic_salary_amt, hra_salary_amt = get_component_amt_from_salary_slip(
					doc.employee,
					assignment.salary_structure,
					basic_component,
					hra_component,
					assignment.from_date,
					frequency,
				)
				to_date = get_end_date_for_assignment(assignment_dates, idx, doc.payroll_period)

				basic_amount += get_component_pay(frequency, basic_salary_amt, assignment.from_date, to_date)
				hra_amount += get_component_pay(frequency, hra_salary_amt, assignment.from_date, to_date)
				months += get_months(assignment.from_date, to_date)

		if hra_amount:
			if doc.monthly_house_rent:
				annual_exemption = calculate_hra_exemption(
					assignment.salary_structure,
					basic_amount,
					hra_amount,
					doc.monthly_house_rent,
					doc.rented_in_metro_city,
					months,
				)
				if annual_exemption > 0:
					monthly_exemption = annual_exemption / months
				else:
					annual_exemption = 0

	return frappe._dict(
		{
			"hra_amount": hra_amount,
			"annual_exemption": annual_exemption,
			"monthly_exemption": monthly_exemption,
		}
	)


def has_hra_component(salary_structure, hra_component):
	return frappe.db.exists(
		"Salary Detail",
		{
			"parent": salary_structure,
			"salary_component": hra_component,
			"parentfield": "earnings",
			"parenttype": "Salary Structure",
		},
	)


def get_end_date_for_assignment(assignment_dates, idx, payroll_period):
	end_date = None

	try:
		end_date = assignment_dates[idx + 1]
		end_date = add_days(end_date, -1)
	except IndexError:
		pass

	if not end_date:
		end_date = frappe.db.get_value("Payroll Period", payroll_period, "end_date")

	return end_date


def get_component_amt_from_salary_slip(
	employee, salary_structure, basic_component, hra_component, from_date, frequency=None
):
	salary_slip = _make_salary_slip(
		salary_structure,
		employee=employee,
		for_preview=1,
		ignore_permissions=True,
		posting_date=get_preview_posting_date(employee, from_date, frequency),
	)

	basic_amt, hra_amt = 0, 0
	for earning in salary_slip.earnings:
		if earning.salary_component == basic_component:
			basic_amt = flt(earning.default_amount) or earning.amount
		elif earning.salary_component == hra_component:
			hra_amt = flt(earning.default_amount) or earning.amount
		if basic_amt and hra_amt:
			return basic_amt, hra_amt
	return basic_amt, hra_amt


def get_preview_posting_date(employee, from_date, frequency):
	# a slip only finds an assignment that starts by the period start, except in the joining period
	from_date = getdate(from_date)
	if from_date == frappe.db.get_value("Employee", employee, "date_of_joining"):
		return from_date

	if frequency == "Monthly" and from_date.day != 1:
		return add_days(get_last_day(from_date), 1)
	if frequency == "Bimonthly" and from_date.day not in (1, 16):
		return from_date.replace(day=16) if from_date.day < 16 else add_days(get_last_day(from_date), 1)

	return from_date


def get_months(from_date, to_date):
	from_date, to_date = getdate(from_date), getdate(to_date)
	months = 0
	while from_date <= to_date:
		month_end = min(get_last_day(from_date), to_date)
		months += (date_diff(month_end, from_date) + 1) / get_last_day(from_date).day
		from_date = add_days(month_end, 1)

	return months


def calculate_hra_exemption(
	salary_structure, annual_basic, annual_hra, monthly_house_rent, rented_in_metro_city, months=12
):
	# TODO make this configurable
	exemptions = []
	# case 1: The actual amount allotted by the employer as the HRA.
	exemptions.append(annual_hra)

	# case 2: Actual rent paid less 10% of the basic salary.
	actual_annual_rent = monthly_house_rent * months
	exemptions.append(flt(actual_annual_rent) - flt(annual_basic * 0.1))

	# case 3: 50% of the basic salary, if the employee is staying in a metro city (40% for a non-metro city).
	exemptions.append(annual_basic * 0.5 if rented_in_metro_city else annual_basic * 0.4)

	# return minimum of 3 cases
	return min(exemptions)


def get_component_pay(frequency, amount, from_date, to_date):
	days = date_diff(to_date, from_date) + 1

	if frequency == "Daily":
		return amount * days
	elif frequency == "Weekly":
		return amount * math.floor(days / 7)
	elif frequency == "Fortnightly":
		return amount * math.floor(days / 14)
	elif frequency == "Monthly":
		return amount * get_months(from_date, to_date)
	elif frequency == "Bimonthly":
		return amount * get_months(from_date, to_date) * 2


def validate_house_rent_dates(doc):
	if not doc.rented_to_date or not doc.rented_from_date:
		frappe.throw(_("House rented dates required for exemption calculation"))

	if date_diff(doc.rented_to_date, doc.rented_from_date) < 14:
		frappe.throw(_("House rented dates should be atleast 15 days apart"))

	start_date, end_date = frappe.db.get_value(
		"Payroll Period", doc.payroll_period, ["start_date", "end_date"]
	)
	if getdate(doc.rented_from_date) < getdate(start_date) or getdate(doc.rented_to_date) > getdate(end_date):
		frappe.throw(
			_("House rented dates should be within the Payroll Period {0} ({1} to {2})").format(
				doc.payroll_period, formatdate(start_date), formatdate(end_date)
			)
		)

	proof = frappe.qb.DocType("Employee Tax Exemption Proof Submission")
	proofs = (
		frappe.qb.from_(proof)
		.select(proof.name)
		.where(
			(proof.docstatus == 1)
			& (proof.employee == doc.employee)
			& (proof.payroll_period == doc.payroll_period)
			& (
				proof.rented_from_date.between(doc.rented_from_date, doc.rented_to_date)
				| proof.rented_to_date.between(doc.rented_from_date, doc.rented_to_date)
			)
		)
	).run()

	if proofs:
		frappe.throw(_("House rent paid days overlapping with {0}").format(proofs[0][0]))


def calculate_hra_exemption_for_period(doc):
	monthly_rent, eligible_hra = 0, 0
	if doc.house_rent_payment_amount:
		validate_house_rent_dates(doc)
		# TODO receive rented months or validate dates are start and end of months?
		# Calc monthly rent, round to nearest .5
		factor = flt(date_diff(doc.rented_to_date, doc.rented_from_date) + 1) / 30
		factor = round(factor * 2) / 2
		monthly_rent = doc.house_rent_payment_amount / factor
		# update field used by calculate_annual_eligible_hra_exemption
		doc.monthly_house_rent = monthly_rent
		exemptions = calculate_annual_eligible_hra_exemption(doc)

		if exemptions["monthly_exemption"]:
			# calc total exemption amount
			eligible_hra = exemptions["monthly_exemption"] * factor
		exemptions["monthly_house_rent"] = monthly_rent
		exemptions["total_eligible_hra_exemption"] = eligible_hra
		return exemptions


def calculate_tax_with_marginal_relief(tax_slab, tax_amount, annual_taxable_earning):
	"""
	Returns the tax payable after applying marginal relief (if applicable).
	    If taxable income is between tax relief limit and marginal relief limit, and tax payable on income is more than income excess over tax relief, then tax payable is reduced to just the excess income.
	"""
	if tax_slab.get("marginal_relief_limit"):
		tax_relief_limit = tax_slab.tax_relief_limit or 0
		marginal_relief_limit = tax_slab.marginal_relief_limit or 0

		if annual_taxable_earning > tax_relief_limit and annual_taxable_earning < marginal_relief_limit:
			income_excess_over_tax_relief = annual_taxable_earning - tax_slab.tax_relief_limit

			if income_excess_over_tax_relief < tax_amount:
				tax_amount = income_excess_over_tax_relief  # marginal relief applies

	return tax_amount
