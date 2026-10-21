# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, getdate

from hrms.hr.doctype.expense_claim.expense_claim import SELF_SERVICE_ROLES
from hrms.hr.utils import validate_active_employee


class TravelRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.travel_itinerary.travel_itinerary import TravelItinerary
		from hrms.hr.doctype.travel_request_costing.travel_request_costing import TravelRequestCosting

		address_of_organizer: DF.Data | None
		amended_from: DF.Link | None
		cell_number: DF.Data | None
		company: DF.Link | None
		cost_center: DF.Link | None
		costings: DF.Table[TravelRequestCosting]
		date_of_birth: DF.Date | None
		description: DF.SmallText | None
		details_of_sponsor: DF.Data | None
		employee: DF.Link
		employee_name: DF.Data | None
		itinerary: DF.Table[TravelItinerary]
		name_of_organizer: DF.Data | None
		other_details: DF.Text | None
		passport_number: DF.Data | None
		personal_id_number: DF.Data | None
		personal_id_type: DF.Link | None
		prefered_email: DF.Data | None
		purpose_of_travel: DF.Link
		travel_funding: DF.Literal[
			"", "Require Full Funding", "Fully Sponsored", "Partially Sponsored, Require Partial Funding"
		]
		travel_proof: DF.Attach | None
		travel_type: DF.Literal["", "Domestic", "International"]
	# end: auto-generated types

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_itinerary_dates()
		self.set_costing_totals()

	def validate_itinerary_dates(self):
		for row in self.itinerary:
			if (
				row.departure_date
				and row.arrival_date
				and get_datetime(row.arrival_date) < get_datetime(row.departure_date)
			):
				frappe.throw(
					_("Row {0}: Arrival Datetime cannot be before Departure Datetime").format(row.idx)
				)

			if (
				row.check_in_date
				and row.check_out_date
				and getdate(row.check_out_date) < getdate(row.check_in_date)
			):
				frappe.throw(_("Row {0}: Check-out Date cannot be before Check-in Date").format(row.idx))

	def set_costing_totals(self):
		for row in self.costings:
			if row.sponsored_amount or row.funded_amount:
				row.total_amount = flt(row.sponsored_amount) + flt(row.funded_amount)


def is_limited_to_own_employee(user: str) -> bool:
	roles = {
		perm.role
		for perm in frappe.permissions.get_valid_perms("Travel Request", user)
		if perm.read and not perm.permlevel
	}
	return not roles - SELF_SERVICE_ROLES


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	if not is_limited_to_own_employee(user):
		return ""

	return f"`tabTravel Request`.`employee` in (select `name` from `tabEmployee` where `user_id` = {frappe.db.escape(user)})"


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not doc.employee or not is_limited_to_own_employee(user):
		return True

	return frappe.db.get_value("Employee", doc.employee, "user_id") == user
