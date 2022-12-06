# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, flt, formatdate, get_last_day, get_last_day_of_week, getdate

from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry


class OverlapError(frappe.ValidationError):
	pass


class AutoLeaveAllocation(Document):
	def validate(self):
		self.validate_dates()
		self.validate_overlap()
		if not self.filters_json:
			self.filters_json = "[]"

	def on_submit(self):
		self.run_allocation()

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
			.where(db_ala.filters_json == self.filters_json)
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
		to_date = min(to_date, getdate(self.end_date))
		conditions = json.loads(self.filters_json) or []
		conditions.append(["Employee", "status", "=", "Active"])
		employees = frappe.db.get_all("Employee", filters=conditions, pluck="name")
		for emp in employees:
			try:
				# get_overlapping_entries only considers super-sets of the leave allocation it plans to create.
				overlapping_entries = get_overlapping_entries(emp, self.leave_type, from_date, to_date)
				if overlapping_entries:
					update_overlapping_leave_allocation(
						overlapping_entries[0][0], self.leave_type, self.new_allocation, from_date, to_date
					)
					continue
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
			except Exception:
				frappe.log_error(
					title=f"Could not auto allocate leave for {emp}", message=str(frappe.get_traceback())
				)
				continue

	@frappe.whitelist()
	def run_allocation(self):
		from_date = getdate(self.start_date)
		to_date = getdate(self.end_date)
		if from_date > getdate():
			return False

		to_date = min(getdate(), to_date)
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


def update_overlapping_leave_allocation(allocation, leave_type, earned_leaves, from_date, to_date):
	leave_type = frappe.get_cached_doc("Leave Type", leave_type)
	allocation = frappe.get_doc("Leave Allocation", allocation)
	new_allocation = flt(allocation.total_leaves_allocated) + flt(earned_leaves)

	if new_allocation > leave_type.max_leaves_allowed and leave_type.max_leaves_allowed > 0:
		new_allocation = leave_type.max_leaves_allowed

	if new_allocation != allocation.total_leaves_allocated:
		allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)
		args = dict(
			leaves=earned_leaves,
			from_date=from_date,
			to_date=to_date,
			is_carry_forward=0,
		)
		create_leave_ledger_entry(allocation, args)

		if leave_type.based_on_date_of_joining:
			text = _("allocated {0} leave(s) via scheduler on {1} based on the date of joining").format(
				frappe.bold(earned_leaves), frappe.bold(formatdate(from_date))
			)
		else:
			text = _("allocated {0} leave(s) via scheduler on {1}").format(
				frappe.bold(earned_leaves), frappe.bold(formatdate(from_date))
			)

		allocation.add_comment(comment_type="Info", text=text)


def get_overlapping_entries(employee, leave_type, from_date, to_date):
	Allocation = frappe.qb.DocType("Leave Allocation")
	return (
		frappe.qb.from_(Allocation)
		.select(Allocation.name)
		.where(
			(Allocation.employee == employee)
			& (Allocation.leave_type == leave_type)
			& (Allocation.docstatus == 1)
			& ((Allocation.from_date <= from_date) & (Allocation.to_date >= to_date))
		)
	).run()
