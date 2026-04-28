# Copyright (c) 2026, contributors
# For license information, please see license.txt

from frappe.model.document import Document


class KoreaSalarySlipExtension(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		employee: DF.Link
		employment_insurance: DF.Currency | None
		engine_version: DF.Data | None
		health_insurance: DF.Currency | None
		income_tax: DF.Currency | None
		linked_calc_reference: DF.Link | None
		local_income_tax: DF.Currency | None
		long_term_care_insurance: DF.Currency | None
		national_pension: DF.Currency | None
		net_pay: DF.Currency | None
		non_taxable_total: DF.Currency | None
		pay_year_month: DF.Data | None
		ruleset_version: DF.Data | None
		salary_slip: DF.Link | None
		tax_method: DF.Select | None
		taxable_total: DF.Currency | None
	# end: auto-generated types

	pass
