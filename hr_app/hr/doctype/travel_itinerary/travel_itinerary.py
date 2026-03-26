# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from frappe.model.document import Document


class TravelItinerary(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		advance_amount: DF.Data | None
		arrival_date: DF.Datetime | None
		check_in_date: DF.Date | None
		check_out_date: DF.Date | None
		departure_date: DF.Datetime | None
		lodging_required: DF.Check
		meal_preference: DF.Literal["", "Vegetarian", "Non-Vegetarian", "Gluten Free", "Non Diary"]
		mode_of_travel: DF.Literal["", "Flight", "Train", "Taxi", "Rented Car"]
		other_details: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		preferred_area_for_lodging: DF.Data | None
		travel_advance_required: DF.Check
		travel_from: DF.Data | None
		travel_to: DF.Data | None
	# end: auto-generated types

	pass
