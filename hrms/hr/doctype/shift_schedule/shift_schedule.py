# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import random_string


class ShiftSchedule(Document):
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
