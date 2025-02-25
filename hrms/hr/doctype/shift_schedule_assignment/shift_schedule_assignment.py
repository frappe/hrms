# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, get_weekday, getdate, nowdate

from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import create_shift_assignment


class ShiftScheduleAssignment(Document):
	def create_shifts(self, start_date: str, end_date: str | None = None) -> None:
		shift_schedule = frappe.get_doc("Shift Schedule", self.shift_schedule)
		gap = {
			"Every Week": 0,
			"Every 2 Weeks": 1,
			"Every 3 Weeks": 2,
			"Every 4 Weeks": 3,
		}[shift_schedule.frequency]

		date = start_date
		individual_assignment_start = None
		week_end_day = get_weekday(getdate(add_days(start_date, -1)))
		repeat_on_days = [day.day for day in shift_schedule.repeat_on_days]

		if not end_date:
			end_date = add_days(start_date, 90)

		while date <= end_date:
			weekday = get_weekday(getdate(date))
			if weekday in repeat_on_days:
				if not individual_assignment_start:
					individual_assignment_start = date
				if date == end_date:
					self.create_individual_assignment(
						shift_schedule.shift_type, individual_assignment_start, date
					)

			elif individual_assignment_start:
				self.create_individual_assignment(
					shift_schedule.shift_type, individual_assignment_start, add_days(date, -1)
				)
				individual_assignment_start = None

			if weekday == week_end_day and gap:
				if individual_assignment_start:
					self.create_individual_assignment(
						shift_schedule.shift_type, individual_assignment_start, date
					)
					individual_assignment_start = None
				date = add_days(date, 7 * gap)

			date = add_days(date, 1)

	def create_individual_assignment(self, shift_type, start_date, end_date):
		create_shift_assignment(
			self.employee,
			self.company,
			shift_type,
			start_date,
			end_date,
			self.shift_status,
			self.shift_location,
			self.name,
		)
		self.create_shifts_after = end_date
		self.save()


def process_auto_shift_creation():
	shift_schedule_assignments = frappe.get_all(
		"Shift Schedule Assignment",
		filters={"enabled": 1, "create_shifts_after": ["<=", nowdate()]},
		pluck="name",
	)
	for d in shift_schedule_assignments:
		doc = frappe.get_doc("Shift Schedule Assignment", d)
		doc.create_shifts(add_days(doc.create_shifts_after, 1))
