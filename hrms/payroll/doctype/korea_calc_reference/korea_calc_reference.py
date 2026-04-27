# Copyright (c) 2026, contributors
# For license information, please see license.txt

from frappe.model.document import Document


class KoreaCalcReference(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		employee_id: DF.Link
		engine_version: DF.Data | None
		import_payload: DF.LongText | None
		imported_at: DF.Datetime | None
		imported_by: DF.Link | None
		kind: DF.Select
		pay_year_month: DF.Data | None
		applied_pay_year_month: DF.Data | None
		retirement_date: DF.Date | None
		ruleset_version: DF.Data | None
		run_id: DF.Data
		salary_slip_external_ref: DF.Data | None
	# end: auto-generated types

	pass
