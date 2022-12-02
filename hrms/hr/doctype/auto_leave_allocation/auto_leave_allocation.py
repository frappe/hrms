# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, get_last_day, get_last_day_of_week, getdate


class OverlapError(frappe.ValidationError):
	pass


class AutoLeaveAllocation(Document):
	def validate(self):
		self.validate_dates()
		self.validate_overlap()
		if not self.filters_json:
			self.filters_json = "[]"

	def on_submit(self):
		# self.run_allocation()
		return

	def validate_dates(self):
		if self.start_date >= self.end_date:
			frappe.throw(_("End date should be greater than start date."))

	def validate_overlap(self):
		db_ala = frappe.qb.DocType("Auto Leave Allocation")
		query = (
			frappe.qb.from_(db_ala)
			.select(db_ala.name)
			.where(db_ala.docstatus != 2)
			.where(db_ala.leave_type == self.leave_type)
			.where(
				((db_ala.start_date >= self.start_date) & (db_ala.start_date <= self.end_date))
				| ((db_ala.end_date >= self.start_date) & (db_ala.end_date <= self.end_date))
				| ((db_ala.start_date <= self.start_date) & (db_ala.end_date >= self.end_date))
			)
		)
		if self.name:
			query = query.where(db_ala.name != self.name)

		overlapping_entries = query.run(pluck=True)
		if overlapping_entries:
			frappe.throw(
				_("The following entries overlaps with this document: {}").format(
					", ".join(overlapping_entries)
				),
				OverlapError,
			)

	def allocate_leave(self, from_date):
		to_date = (
			get_last_day(from_date) if self.frequency == "Monthly" else get_last_day_of_week(from_date)
		)
		conditions = json.loads(self.filters_json) or []
		conditions.append(["Employee", "status", "=", "Active"])
		employees = frappe.db.get_all("Employee", filters=conditions, pluck="name")
		for emp in employees:
			try:
				frappe.get_doc(
					{
						"doctype": "Leave Allocation",
						"employee": emp,
						"leave_type": self.leave_type,
						"from_date": from_date,
						"to_date": to_date,
						"new_leaves_allocated": self.new_allocation,
						"carry_forward": self.carry_forward,
						"auto_leave_allocation": self.name,
					}
				).submit()
			except Exception as e:
				frappe.log_error(title=f"Could not auto allocate leave for {emp}", message=str(e))
				continue

	@frappe.whitelist()
	def run_allocation(self):
		self.start_date = getdate(self.start_date)
		self.end_date = getdate(self.end_date)
		if self.start_date > getdate():
			return

		to_date = min(getdate(), self.end_date)
		from_date = self.start_date
		last_day = get_last_day if self.frequency == "Monthly" else get_last_day_of_week

		while from_date <= to_date:
			self.allocate_leave(from_date=from_date)
			from_date = last_day(from_date)
			from_date = add_to_date(from_date, days=1)

		return True


def process_auto_leave_allocation(frequency):
	today = getdate()
	db_ala = frappe.qb.DocType("Auto Leave Allocation")
	active_ala = (
		frappe.qb.from_(db_ala)
		.select(db_ala.name)
		.where(db_ala.docstatus == 1)
		.where(db_ala.frequency == frequency)
		.where(db_ala.start_date <= today)
		.where(db_ala.end_date >= today)
		.run(pluck=True)
	)
	frappe.log_error(str(active_ala))
	for ala in active_ala:
		frappe.get_doc("Auto Leave Allocation", ala).allocate_leave(today)


def process_weekly_auto_leave_allocation():
	process_auto_leave_allocation("Weekly")


def process_monthly_auto_leave_allocation():
	process_auto_leave_allocation("Monthly")
