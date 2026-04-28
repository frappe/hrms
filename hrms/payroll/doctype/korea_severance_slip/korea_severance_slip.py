# Copyright (c) 2026, contributors
# For license information, please see license.txt

from frappe.model.document import Document


class KoreaSeveranceSlip(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		average_wage: DF.Currency | None
		employee: DF.Link
		engine_version: DF.Data | None
		external_run_id: DF.Data
		linked_calc_reference: DF.Link | None
		linked_salary_slip: DF.Link | None
		local_income_tax: DF.Currency | None
		net_pay: DF.Currency | None
		retirement_date: DF.Date
		ruleset_version: DF.Data | None
		severance_income_tax: DF.Currency | None
		severance_pay: DF.Currency | None
		service_years: DF.Float | None
	# end: auto-generated types

	pass
