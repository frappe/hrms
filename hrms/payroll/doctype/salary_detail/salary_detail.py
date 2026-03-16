# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class SalaryDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		abbr: DF.Data | None
		accrual_component: DF.Check
		additional_amount: DF.Currency
		additional_salary: DF.Link | None
		amount: DF.Currency
		amount_based_on_formula: DF.Check
		condition: DF.Code | None
		deduct_full_tax_on_selected_payroll_date: DF.Check
		default_amount: DF.Currency
		depends_on_payment_days: DF.Check
		do_not_include_in_accounts: DF.Check
		do_not_include_in_total: DF.Check
		exempted_from_income_tax: DF.Check
		formula: DF.Code | None
		is_flexible_benefit: DF.Check
		is_recurring_additional_salary: DF.Check
		is_tax_applicable: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		salary_component: DF.Link
		statistical_component: DF.Check
		tax_on_additional_salary: DF.Currency
		tax_on_flexible_benefit: DF.Currency
		variable_based_on_taxable_salary: DF.Check
		year_to_date: DF.Currency
	# end: auto-generated types

	pass
