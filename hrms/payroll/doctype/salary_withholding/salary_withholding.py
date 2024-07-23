# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import date

from dateutil.relativedelta import relativedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_to_date, cint, get_link_to_form, getdate


class SalaryWithholding(Document):
	def validate(self):
		if not self.payroll_frequency:
			self.payroll_frequency = get_payroll_frequency(self.employee, self.from_date)

		self.set_withholding_cycles_and_to_date()
		self.validate_duplicate_record()
		self.set_status()

	def validate_duplicate_record(self):
		Withholding = frappe.qb.DocType("Salary Withholding")
		duplicate = (
			frappe.qb.from_(Withholding)
			.select(Withholding.name)
			.where(
				(Withholding.employee == self.employee)
				& (Withholding.docstatus != 2)
				& (Withholding.name != self.name)
				& (Withholding.to_date >= self.from_date)
				& (Withholding.from_date <= self.to_date)
			)
		).run(pluck=True)

		if duplicate:
			frappe.throw(
				_("Salary Withholding {0} already exists for employee {1} for the selected period").format(
					get_link_to_form("Salary Withholding", duplicate[0]),
					frappe.bold(f"{self.employee}: {self.employee_name}"),
				),
				title=_("Duplicate Salary Withholding"),
			)

	def set_status(self, update=False):
		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			if all(cycle.is_salary_released for cycle in self.cycles):
				status = "Released"
			else:
				status = "Withheld"
		elif self.docstatus == 2:
			status = "Cancelled"

		if update:
			self.db_set("status", status)
		else:
			self.status = status

	@frappe.whitelist()
	def set_withholding_cycles_and_to_date(self):
		self.to_date = self.get_to_date()

		cycle_from_date = cycle_to_date = getdate(self.from_date)
		self.cycles = []

		while cycle_to_date < getdate(self.to_date):
			cycle_to_date = add_to_date(cycle_from_date, **self.get_frequency_kwargs()) - relativedelta(
				days=1
			)
			self.append(
				"cycles",
				{
					"from_date": cycle_from_date,
					"to_date": cycle_to_date,
					"is_salary_released": 0,
				},
			)
			cycle_from_date = add_days(cycle_to_date, 1)

	def get_to_date(self) -> str:
		from_date = getdate(self.from_date)
		kwargs = self.get_frequency_kwargs(self.number_of_withholding_cycles)
		to_date = add_to_date(from_date, **kwargs) - relativedelta(days=1)
		return to_date

	def get_frequency_kwargs(self, withholding_cycles: int = 0) -> dict:
		cycles = cint(withholding_cycles) or 1
		frequency_dict = {
			"Monthly": {"months": 1 * cycles},
			"Bimonthly": {"months": 2 * cycles},
			"Fortnightly": {"days": 14 * cycles},
			"Weekly": {"days": 7 * cycles},
			"Daily": {"days": 1 * cycles},
		}
		return frequency_dict.get(self.payroll_frequency)


@frappe.whitelist()
def get_payroll_frequency(employee: str, posting_date: str | date) -> str | None:
	salary_structure = frappe.db.get_value(
		"Salary Structure Assignment",
		{
			"employee": employee,
			"from_date": ("<=", posting_date),
			"docstatus": 1,
		},
		"salary_structure",
		order_by="from_date desc",
	)

	if not salary_structure:
		frappe.throw(
			_("No Salary Structure Assignment found for employee {0} on or before {1}").format(
				employee, posting_date
			),
			title=_("Error"),
		)

	return frappe.db.get_value("Salary Structure", salary_structure, "payroll_frequency")


def link_bank_entry_in_salary_withholdings(salary_slips: list[dict], bank_entry: str):
	WithholdingCycle = frappe.qb.DocType("Salary Withholding Cycle")
	(
		frappe.qb.update(WithholdingCycle)
		.set(WithholdingCycle.journal_entry, bank_entry)
		.where(
			WithholdingCycle.name.isin([salary_slip.salary_withholding_cycle for salary_slip in salary_slips])
		)
	).run()


def update_salary_withholding_payment_status(doc: "SalaryWithholding", method: str | None = None):
	"""update withholding status on bank entry submission/cancellation. Called from hooks"""
	Withholding = frappe.qb.DocType("Salary Withholding")
	WithholdingCycle = frappe.qb.DocType("Salary Withholding Cycle")
	withholdings = (
		frappe.qb.from_(WithholdingCycle)
		.inner_join(Withholding)
		.on(WithholdingCycle.parent == Withholding.name)
		.select(
			WithholdingCycle.name.as_("salary_withholding_cycle"),
			WithholdingCycle.parent.as_("salary_withholding"),
			Withholding.employee,
		)
		.where((WithholdingCycle.journal_entry == doc.name) & (WithholdingCycle.docstatus == 1))
	).run(as_dict=True)

	if not withholdings:
		return

	cancel = method == "on_cancel"
	_update_payment_status_in_payroll(withholdings, cancel=cancel)
	_update_salary_withholdings(withholdings, cancel=cancel)


def _update_payment_status_in_payroll(withholdings: list[dict], cancel: bool = False) -> None:
	status = "Withheld" if cancel else "Submitted"

	SalarySlip = frappe.qb.DocType("Salary Slip")
	(
		frappe.qb.update(SalarySlip)
		.set(SalarySlip.status, status)
		.where(
			SalarySlip.salary_withholding_cycle.isin(
				[withholding.salary_withholding_cycle for withholding in withholdings]
			)
		)
	).run()

	employees = [withholding.employee for withholding in withholdings]
	is_salary_withheld = 1 if cancel else 0
	PayrollEmployee = frappe.qb.DocType("Payroll Employee Detail")
	(
		frappe.qb.update(PayrollEmployee)
		.set(PayrollEmployee.is_salary_withheld, is_salary_withheld)
		.where(PayrollEmployee.employee.isin(employees))
	).run()


def _update_salary_withholdings(withholdings: list[dict], cancel: bool = False) -> None:
	is_salary_released = 0 if cancel else 1

	for withholding in withholdings:
		withholding_doc = frappe.get_doc("Salary Withholding", withholding.salary_withholding)
		for cycle in withholding_doc.cycles:
			if cycle.name == withholding.salary_withholding_cycle:
				cycle.db_set("is_salary_released", is_salary_released)
				if cancel:
					cycle.db_set("journal_entry", None)
				break

		withholding_doc.set_status(update=True)
