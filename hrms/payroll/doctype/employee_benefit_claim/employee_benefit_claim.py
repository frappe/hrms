# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form, getdate

from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period
from hrms.payroll.doctype.salary_slip.salary_slip import get_benefits_details_parent
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	get_assigned_salary_structure,
)


class EmployeeBenefitClaim(Document):
	def validate(self):
		self.validate_date_and_benefit_claim_amount()
		self.validate_duplicate_claim()

	def validate_date_and_benefit_claim_amount(self):
		if getdate(self.payroll_date) < getdate():
			frappe.throw(
				_(
					"Payroll date cannot be in the past. This is to ensure that claims are made for the current or future payroll cycles."
				)
			)

		if self.claimed_amount <= 0:
			frappe.throw(_("Claimed amount of employee {0} should be greater than 0").format(self.employee))

		if self.claimed_amount > self.max_amount_eligible:
			frappe.throw(
				_("Claimed amount of employee {0} exceeds maximum amount eligible for claim {1}").format(
					self.employee, self.max_amount_eligible
				)
			)

	def validate_duplicate_claim(self):
		"""
		Since Employee Benefit Ledger entries are only created upon Salary Slip submission,
		there is a risk of multiple claims being created for the same benefit component within
		one payroll cycle, and combined claim amount exceeding the maximum eligible amount.
		So limit the claim to one per month.
		"""
		existing_claim = self.get_existing_claim_for_month()
		if existing_claim:
			msg = _(
				"Employee {0} has already claimed the benefit '{1}' for {2} ({3}).<br>"
				"To prevent overpayments, only one claim per benefit type is allowed in each payroll cycle."
			).format(
				frappe.bold(self.employee),
				frappe.bold(self.earning_component),
				frappe.bold(frappe.utils.formatdate(self.payroll_date, "MMMM yyyy")),
				frappe.bold(get_link_to_form("Employee Benefit Claim", existing_claim)),
			)
			frappe.throw(msg, title=_("Duplicate Claim Detected"))

	def on_submit(self):
		self.create_additional_salary()

	def get_existing_claim_for_month(self):
		month_start_date = frappe.utils.get_first_day(self.payroll_date)
		month_end_date = frappe.utils.get_last_day(self.payroll_date)

		return frappe.db.get_value(
			"Employee Benefit Claim",
			{
				"employee": self.employee,
				"earning_component": self.earning_component,
				"payroll_date": ["between", [month_start_date, month_end_date]],
				"docstatus": 1,
				"name": ["!=", self.name],
			},
			"name",
		)

	def create_additional_salary(self):
		frappe.get_doc(
			{
				"doctype": "Additional Salary",
				"company": self.company,
				"employee": self.employee,
				"currency": self.currency,
				"salary_component": self.earning_component,
				"payroll_date": self.payroll_date,
				"amount": self.claimed_amount,
				"overwrite_salary_structure_amount": 0,
				"ref_doctype": self.doctype,
				"ref_docname": self.name,
			}
		).submit()

	@frappe.whitelist()
	def get_benefit_details(self):
		# Fetch max benefit amount and claimable amount for the employee based on the earning component chosen
		from hrms.payroll.doctype.employee_benefit_ledger.employee_benefit_ledger import (
			get_max_claim_eligible,
		)

		payroll_period = get_payroll_period(self.payroll_date, self.payroll_date, self.company).get("name")
		salary_structure_assignment = get_salary_structure_assignment(self.employee, self.payroll_date)
		component_details = self.get_component_details(payroll_period, salary_structure_assignment)

		yearly_benefit = 0
		claimable_benefit = 0

		if component_details:
			current_month_amount = self._get_current_month_benefit_amount(component_details)
			yearly_benefit = component_details.get("amount", 0)
			claimable_benefit = get_max_claim_eligible(
				self.employee, payroll_period, component_details, current_month_amount
			)

		self.yearly_benefit = yearly_benefit
		self.max_amount_eligible = claimable_benefit

	def get_component_details(self, payroll_period, salary_structure_assignment):
		# Get component details from benefit parent document
		benefit_details_parent, benefit_details_doctype = get_benefits_details_parent(
			self.employee, payroll_period, salary_structure_assignment
		)

		if not benefit_details_parent:
			return None

		EmployeeBenefitDetail = frappe.qb.DocType(benefit_details_doctype)
		SalaryComponent = frappe.qb.DocType("Salary Component")

		component_details = (
			frappe.qb.from_(EmployeeBenefitDetail)
			.join(SalaryComponent)
			.on(SalaryComponent.name == EmployeeBenefitDetail.salary_component)
			.select(
				SalaryComponent.name,
				SalaryComponent.payout_method,
				SalaryComponent.depends_on_payment_days,
				EmployeeBenefitDetail.amount,
			)
			.where(SalaryComponent.name == self.earning_component)
			.where(EmployeeBenefitDetail.parent == benefit_details_parent)
		).run(as_dict=True)

		return component_details[0] if component_details else None

	def _get_current_month_benefit_amount(self, component_details: dict) -> float:
		# Get current month benefit amount if payout method requires it
		payout_method = component_details.get("payout_method")
		if payout_method == "Accrue per cycle, pay only on claim":
			return self.preview_salary_slip_and_fetch_current_month_benefit_amount()
		return 0.0

	def preview_salary_slip_and_fetch_current_month_benefit_amount(self):
		"""Preview salary slip and fetch current month benefit amount for accrual components."""
		from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

		salary_structure = get_assigned_salary_structure(self.employee, self.payroll_date)
		salary_slip = make_salary_slip(
			salary_structure, employee=self.employee, posting_date=self.payroll_date, for_preview=1
		)
		accrued_benefits = salary_slip.get("accrued_benefits", [])
		for benefit in accrued_benefits:
			if benefit.get("salary_component") == self.earning_component:
				return benefit.get("amount", 0)
		return 0


@frappe.whitelist()
def get_benefit_components(doctype, txt, searchfield, start, page_len, filters):
	"""Fetch benefit components to choose from based on employee and date filters."""
	employee = filters.get("employee")
	date = filters.get("date")
	company = filters.get("company")

	if not employee or not date:
		return []

	try:
		salary_structure_assignment = get_salary_structure_assignment(employee, date)
		payroll_period = get_payroll_period(date, date, company).get("name")

		benefit_details_parent, benefit_details_doctype = get_benefits_details_parent(
			employee, payroll_period, salary_structure_assignment
		)

		if not benefit_details_parent:
			return []

		SalaryComponent = frappe.qb.DocType("Salary Component")
		EmployeeBenefitDetail = frappe.qb.DocType(benefit_details_doctype)
		return (
			frappe.qb.from_(EmployeeBenefitDetail)
			.join(SalaryComponent)
			.on(SalaryComponent.name == EmployeeBenefitDetail.salary_component)
			.select(EmployeeBenefitDetail.salary_component)
			.where(EmployeeBenefitDetail.parent == benefit_details_parent)
			.where(
				SalaryComponent.payout_method.isin(
					["Accrue per cycle, pay only on claim", "Allow claim for full benefit amount"]
				)
			)
		).run()

	except Exception as e:
		frappe.log_error("Error fetching benefit components", e)
		return []


def get_salary_structure_assignment(employee, date):
	SalaryStructureAssignment = frappe.qb.DocType("Salary Structure Assignment")
	result = (
		frappe.qb.from_(SalaryStructureAssignment)
		.select(SalaryStructureAssignment.name)
		.where(SalaryStructureAssignment.employee == employee)
		.where(SalaryStructureAssignment.docstatus == 1)
		.where(SalaryStructureAssignment.from_date <= date)
		.orderby(SalaryStructureAssignment.from_date, order=frappe.qb.desc)
		.limit(1)
	).run(pluck="name")

	if not result:
		frappe.throw(
			_("Salary Structure Assignment not found for employee {0} on date {1}").format(employee, date)
		)

	return result[0]
