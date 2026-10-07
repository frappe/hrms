# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import notify_assignment
from frappe.utils import add_days, get_link_to_form

from hrms.hr.doctype.employee_onboarding_activity.employee_onboarding_activity import (
	get_standard_activities,
)

ASSIGNMENTS = {
	"Holiday List Assignment": {
		"master": "Holiday List",
		"offer_field": "holiday_list",
		"employee_field": "assigned_to",
		"filters": {"applicable_for": "Employee"},
	},
	"Leave Policy Assignment": {
		"master": "Leave Policy",
		"offer_field": "leave_policy",
		"employee_field": "employee",
	},
	"Salary Structure Assignment": {
		"master": "Salary Structure",
		"offer_field": "salary_structure",
		"employee_field": "employee",
	},
	"Shift Assignment": {"master": "Shift Type", "employee_field": "employee"},
	"Shift Schedule Assignment": {"master": "Shift Schedule", "employee_field": "employee"},
}

ACTION_DOCTYPES = {
	"Create User": "User",
	"Appointment Letter": "Appointment Letter",
	"Create Employee": "Employee",
}

FINISHED = ("Completed", "Skipped")


class OnboardingActivities:
	"""The checklist rows of an Employee Onboarding.

	Standard activities are always on the onboarding, ahead of the template's own rows. A row
	with an action is completed by the record it creates, not by whoever ticks it; only Manual
	rows are completed by hand. Row changes are written per row, so several people can work
	the same onboarding at once without one save overwriting another.
	"""

	def set_activities(self):
		rows = {row.activity: row for row in self.activities if row.activity}
		standard = [
			rows.get(activity.name) or self.make_activity_row(activity)
			for activity in get_standard_activities()
		]
		standard_names = {row.activity for row in standard}
		others = [row for row in self.activities if row.activity not in standard_names]

		self.activities = []
		for idx, row in enumerate(standard + others, start=1):
			child = self.append("activities", row)
			child.idx = idx
			self.set_activity_defaults(child)

	def make_activity_row(self, activity) -> dict:
		return frappe._dict(
			activity=activity.name,
			activity_name=activity.title,
			description=activity.description,
			user=activity.user,
			begin_on=activity.begin_on,
		)

	def set_activity_defaults(self, row):
		if row.activity:
			master = frappe.get_cached_doc("Employee Onboarding Activity", row.activity)
			row.action = master.action
			row.reference_doctype = master.reference_doctype
			row.depends_on_activity = master.depends_on_activity
		row.action = row.action or "Manual"
		if row.action in ACTION_DOCTYPES:
			row.reference_doctype = ACTION_DOCTYPES[row.action]
		row.status = row.status or ("Completed" if row.completed else "Pending")
		if not row.due_date and self.boarding_begins_on:
			row.due_date = add_days(self.boarding_begins_on, row.begin_on or 0)

	def validate_unique_activities(self):
		seen = set()
		for row in self.activities:
			if row.action == "Manual" and not row.activity:
				continue
			key = row.activity or (row.action, row.reference_doctype)
			if key in seen:
				frappe.throw(
					_("Row #{0}: {1} is already on this onboarding").format(row.idx, row.activity_name)
				)
			seen.add(key)

	def reconcile_activities(self) -> list:
		"""Derive each row's status from the records it creates, and return the changed rows."""
		changed = []
		for row in self.activities:
			status, reference_name = self.get_activity_state(row)
			if (row.status, row.reference_name) != (status, reference_name):
				row.status, row.reference_name = status, reference_name
				row.completed = int(status == "Completed")
				changed.append(row)
		return changed

	def get_activity_state(self, row) -> tuple[str, str | None]:
		if row.action == "Manual" or row.status == "Skipped":
			return row.status, row.reference_name

		reference_name = None
		match row.action:
			case "Create User":
				reference_name = self.user
				done = bool(self.user)
			case "Appointment Letter":
				reference_name = self.appointment_letter
				done = bool(self.appointment_letter_sent_on)
			case "Create Employee":
				reference_name = self.employee
				done = bool(self.employee)
			case "Assign":
				reference_name = self.get_assignment(row.reference_doctype)
				done = bool(reference_name)
			case _:
				done = False
		return ("Completed" if done else "Pending"), reference_name

	def get_assignment(self, doctype: str) -> str | None:
		config = ASSIGNMENTS.get(doctype)
		if not (config and self.employee):
			return None

		filters = {config["employee_field"]: self.employee, **config.get("filters", {})}
		filters["docstatus"] = 1 if frappe.get_meta(doctype).is_submittable else 0
		return frappe.db.get_value(doctype, filters, "name")

	def get_offer_defaults(self) -> dict:
		if not self.job_offer:
			return {}

		offer_fields = [config["offer_field"] for config in ASSIGNMENTS.values() if "offer_field" in config]
		offer = frappe.db.get_value("Job Offer", self.job_offer, offer_fields, as_dict=True) or {}
		return {
			doctype: {
				"fieldname": frappe.scrub(config["master"]),
				"value": offer.get(config.get("offer_field")),
			}
			for doctype, config in ASSIGNMENTS.items()
			if offer.get(config.get("offer_field"))
		}

	def save_activity_states(self):
		"""Persist reconciled rows and the status without saving the whole onboarding."""
		for row in self.reconcile_activities():
			row.db_update()
		self.set_boarding_status()
		self.db_set("boarding_status", self.boarding_status)
		self.sync_todos()

	def set_boarding_status(self):
		if self.boarding_status == "Completed":
			return

		statuses = [row.status for row in self.activities]
		if statuses and all(status in FINISHED for status in statuses):
			self.boarding_status = "Completed"
		elif "Completed" in statuses:
			self.boarding_status = "In Process"
		else:
			self.boarding_status = "Pending"

	def sync_todos(self):
		"""Give every open, assigned row a ToDo of its own, and close those of finished rows."""
		if self.is_new():
			return

		for row in self.activities:
			if row.todo and (row.status in FINISHED or not row.user):
				close_todo(row.todo, "Closed" if row.status in FINISHED else "Cancelled")
				row.db_set("todo", None)
			elif row.user and not row.todo and row.status not in FINISHED:
				row.db_set("todo", self.make_todo(row))

	def make_todo(self, row) -> str:
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": row.user,
				"assigned_by": frappe.session.user,
				"reference_type": self.doctype,
				"reference_name": self.name,
				"description": f"{_(row.activity_name)}: {self.employee_name}",
				"date": row.due_date,
			}
		).insert(ignore_permissions=True)
		notify_assignment(
			todo.assigned_by, todo.allocated_to, self.doctype, self.name, "ASSIGN", todo.description
		)
		return todo.name

	def get_activity(self, row: str):
		activities = self.get("activities", {"name": row})
		if not activities:
			frappe.throw(_("Unknown activity {0}").format(row))
		return activities[0]

	@frappe.whitelist(methods=["POST"])
	def assign_activity(self, row: str, user: str | None = None) -> None:
		self.check_permission("write")
		activity = self.get_activity(row)
		if activity.todo:
			close_todo(activity.todo, "Cancelled")
			activity.db_set("todo", None)
		activity.db_set("user", user or None)
		self.sync_todos()

	@frappe.whitelist(methods=["POST"])
	def set_activity_due_date(self, row: str, due_date: str | None = None) -> None:
		self.check_permission("write")
		activity = self.get_activity(row)
		activity.db_set("due_date", due_date or None)
		if activity.todo:
			frappe.db.set_value("ToDo", activity.todo, "date", due_date or None)

	@frappe.whitelist(methods=["POST"])
	def complete_activity(self, row: str) -> None:
		self.check_permission("write")
		activity = self.get_activity(row)
		if activity.action != "Manual":
			frappe.throw(_("{0} is completed by its own record").format(activity.activity_name))
		self.set_activity_status(activity, "Completed")

	@frappe.whitelist(methods=["POST"])
	def skip_activity(self, row: str) -> None:
		self.check_permission("write")
		self.set_activity_status(self.get_activity(row), "Skipped")

	@frappe.whitelist(methods=["POST"])
	def sync_activities(self) -> None:
		self.check_permission("write")
		self.save_activity_states()

	def set_activity_status(self, activity, status: str):
		activity.db_set({"status": status, "completed": int(status == "Completed")})
		self.save_activity_states()

	def complete_remaining_activities(self):
		for row in self.activities:
			if row.status not in FINISHED:
				row.status = "Completed" if row.action == "Manual" else "Skipped"
				row.completed = int(row.status == "Completed")
		self.boarding_status = "Completed"


def close_todo(name: str, status: str) -> None:
	todo = frappe.get_doc("ToDo", name)
	if todo.status != "Open":
		return
	todo.status = status
	todo.save(ignore_permissions=True)
	if status == "Cancelled":
		notify_assignment(todo.assigned_by, todo.allocated_to, todo.reference_type, todo.reference_name)


def validate_template_activities(template) -> None:
	standard = {activity.name for activity in get_standard_activities()}
	seen = set()
	for row in template.activities:
		if row.activity in standard:
			frappe.throw(
				_("Row #{0}: {1} is a standard activity, which every onboarding already has").format(
					row.idx, get_link_to_form("Employee Onboarding Activity", row.activity)
				)
			)
		if row.activity and row.activity in seen:
			frappe.throw(_("Row #{0}: {1} is listed twice").format(row.idx, row.activity))
		seen.add(row.activity)
