# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from dateutil.relativedelta import relativedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_to_date, cint, getdate


class SalaryWithholding(Document):
	def validate(self):
		self.set_status()

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
def get_payroll_frequency(employee: str, posting_date: str) -> str | None:
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
