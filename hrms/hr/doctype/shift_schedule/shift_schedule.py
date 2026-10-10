# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, get_weekday, getdate, random_string


class ShiftSchedule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.automation.doctype.assignment_rule_day.assignment_rule_day import AssignmentRuleDay
		from frappe.types import DF

		amended_from: DF.Link | None
		frequency: DF.Literal["Every Week", "Every 2 Weeks", "Every 3 Weeks", "Every 4 Weeks"]
		repeat_on_days: DF.Table[AssignmentRuleDay]
		shift_type: DF.Link
	# end: auto-generated types

	def before_validate(self):
		to_be_deleted = []
		seen_days = set()

		for d in self.repeat_on_days:
			if d.day in seen_days:
				to_be_deleted.append(d)
			else:
				seen_days.add(d.day)

		for d in to_be_deleted:
			self.remove(d)

	def get_shift_assignment_dates(self, start_date: str, end_date: str | None = None):
		"""Yield the date ranges created for this schedule, including its rotation gaps."""
		gap = {
			"Every Week": 0,
			"Every 2 Weeks": 1,
			"Every 3 Weeks": 2,
			"Every 4 Weeks": 3,
		}[self.frequency]

		start_date = getdate(start_date)
		date = start_date
		individual_assignment_start = None
		week_end_day = get_weekday(getdate(add_days(start_date, -1)))
		repeat_on_days = [day.day for day in self.repeat_on_days]

		if not end_date:
			end_date = add_days(start_date, 90)
		else:
			end_date = getdate(end_date)

		while date <= end_date:
			weekday = get_weekday(getdate(date))
			if weekday in repeat_on_days:
				if not individual_assignment_start:
					individual_assignment_start = date
				if date == end_date:
					yield individual_assignment_start, date
					individual_assignment_start = None

			elif individual_assignment_start:
				yield individual_assignment_start, add_days(date, -1)
				individual_assignment_start = None

			if weekday == week_end_day and gap:
				if individual_assignment_start:
					yield individual_assignment_start, date
					individual_assignment_start = None
				date = add_days(date, 7 * gap)

			date = add_days(date, 1)


def get_or_insert_shift_schedule(shift_type: str, frequency: str, repeat_on_days: list[str]) -> str:
	shift_schedules = frappe.get_all(
		"Shift Schedule",
		pluck="name",
		filters={"shift_type": shift_type, "frequency": frequency, "docstatus": 1},
	)

	for shift_schedule in shift_schedules:
		shift_schedule = frappe.get_doc("Shift Schedule", shift_schedule)
		shift_schedule_days = [d.day for d in shift_schedule.repeat_on_days]
		if sorted(repeat_on_days) == sorted(shift_schedule_days):
			return shift_schedule.name

	doc = frappe.get_doc(
		{
			"doctype": "Shift Schedule",
			"name": random_string(10),
			"shift_type": shift_type,
			"frequency": frequency,
			"repeat_on_days": [{"day": day} for day in repeat_on_days],
		}
	).insert()
	doc.submit()
	return doc.name
