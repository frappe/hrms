# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, format_date, get_link_to_form, get_weekday, getdate, nowdate

from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import create_shift_assignment


class ShiftScheduleAssignment(Document):
	def validate(self):
		self.validate_existing_shift_assignments()

	def validate_existing_shift_assignments(self):
		if self.has_value_changed("create_shifts_after") and not self.is_new():
			existing_shift_assignments, last_shift_end_date = self.get_existing_shift_assignments()
			if existing_shift_assignments:
				frappe.throw(
					msg=_(
						"Shift assignments for {0} after {1} are already created. Please change {2} date to a date later than {3} {4}"
					).format(
						frappe.bold(self.shift_schedule),
						frappe.bold(self.create_shifts_after),
						frappe.bold("Create Shifts After"),
						frappe.bold(last_shift_end_date),
						(
							"<br><br><ul><li>"
							+ "</li><li>".join(
								get_link_to_form("Shift Assignment", shift)
								for shift in existing_shift_assignments
							)
							+ "</li></ul>"
						),
					),
					title=_("Existing Shift Assignments"),
				)

	def get_existing_shift_assignments(self):
		shift_schedule_assignment = frappe.qb.DocType("Shift Schedule Assignment")
		shift_assignment = frappe.qb.DocType("Shift Assignment")

		query = (
			frappe.qb.from_(shift_assignment)
			.inner_join(shift_schedule_assignment)
			.on(shift_assignment.shift_schedule_assignment == shift_schedule_assignment.name)
			.select(shift_assignment.name, shift_assignment.end_date)
			.where(
				(shift_assignment.end_date >= self.create_shifts_after)
				& (shift_assignment.status == "Active")
				& (shift_assignment.employee == self.employee)
			)
			.orderby(shift_assignment.end_date)
		)

		existing_shifts = query.run(as_dict=True)

		existing_shift_assignments = [shift.name for shift in existing_shifts]
		last_shift_end_date = existing_shifts[-1].end_date if existing_shifts else None

		return existing_shift_assignments, last_shift_end_date

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
		self.db_set("create_shifts_after", end_date, update_modified=False)


def process_auto_shift_creation():
	shift_schedule_assignments = frappe.get_all(
		"Shift Schedule Assignment",
		filters={"enabled": 1, "create_shifts_after": ["<=", nowdate()]},
		pluck="name",
	)
	for d in shift_schedule_assignments:
		try:
			doc = frappe.get_doc("Shift Schedule Assignment", d)

			start_date = doc.create_shifts_after

			doc.create_shifts(add_days(doc.create_shifts_after, 1))

			text = _(
				"Shift Assignments created for the schedule between {0} and {1} via background job"
			).format(frappe.bold(format_date(start_date)), frappe.bold(format_date(doc.create_shifts_after)))

			doc.add_comment(comment_type="Info", text=text)
		except Exception as e:
			frappe.log_error(e)

			continue
