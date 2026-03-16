# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document

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
