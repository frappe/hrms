# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import notify_assignment
from frappe.query_builder import Order
from frappe.query_builder.functions import IfNull
from frappe.utils import add_days

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

PROGRESS_STATUSES = ("In Progress", "Stuck")

TEMPLATE_MATCH_FIELDS = ("company", "department", "designation", "employee_grade")

TEMPLATE_ROW_FIELDS = [
	"activity_name",
	"action",
	"reference_doctype",
	"depends_on_action",
	"user",
	"role",
	"description",
	"begin_on",
	"duration",
]


def make_assign_activity(title, doctype):
	return {
		"activity_name": title,
		"action": "Assign",
		"reference_doctype": doctype,
		"depends_on_action": "Create Employee",
	}


# The tasks the checklist can do itself. Each new template starts with them.
STANDARD_ACTIVITIES = [
	{"activity_name": "Create User", "action": "Create User"},
	{"activity_name": "Create Employee", "action": "Create Employee"},
	{"activity_name": "Appointment Letter", "action": "Appointment Letter"},
	make_assign_activity("Assign Holiday List", "Holiday List Assignment"),
	make_assign_activity("Assign Leave Policy", "Leave Policy Assignment"),
	make_assign_activity("Assign Salary Structure", "Salary Structure Assignment"),
	make_assign_activity("Assign Shift Type", "Shift Assignment"),
	make_assign_activity("Assign Shift Schedule", "Shift Schedule Assignment"),
]


class OnboardingActivities:
	"""The checklist rows of an Employee Onboarding.

	The rows come from the onboarding's template only, so HR decides there which standard
	activities an onboarding gets and who each one is assigned to.
	A row with an action is completed by the record it creates, not by whoever ticks it; only
	Manual rows are completed by hand. An unfinished row may carry a status, In Progress or Stuck.
	Row changes are written per row, so several people can work the same onboarding at once
	without one save overwriting another.
	"""

	def set_template(self):
		if not self.employee_onboarding_template:
			self.employee_onboarding_template = get_matching_template(self)

	def set_activities(self):
		if not self.activities:
			for row in get_template_activities(self.employee_onboarding_template):
				self.append("activities", row)
		for row in self.activities:
			self.set_activity_defaults(row)

	def set_activity_defaults(self, row):
		set_action_defaults(row)
		if row.status not in PROGRESS_STATUSES or is_finished(row):
			row.status = None
		if not row.due_date and self.boarding_begins_on:
			row.due_date = add_days(self.boarding_begins_on, row.begin_on or 0)

	def validate_unique_activities(self):
		validate_unique_actions(self.activities, _("this onboarding"))

	def get_template_hint(self) -> str | None:
		"""The onboarding's template, while it still has only the standard activities."""
		template = self.employee_onboarding_template
		if not template:
			return None
		has_own_rows = frappe.db.exists(
			"Employee Boarding Activity",
			{"parent": template, "parenttype": "Employee Onboarding Template", "action": "Manual"},
		)
		return None if has_own_rows else template

	def reconcile_activities(self) -> list:
		"""Complete each row whose record exists, and return the changed rows."""
		changed = []
		for row in self.activities:
			completed, reference_name = self.get_activity_state(row)
			if (row.completed, row.reference_name) != (completed, reference_name):
				row.completed, row.reference_name = completed, reference_name
				if completed:
					row.status = None
				changed.append(row)
		return changed

	def get_activity_state(self, row) -> tuple[int, str | None]:
		if row.action == "Manual" or row.skipped:
			return row.completed, row.reference_name

		reference_name = None
		match row.action:
			case "Create User":
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
		return int(done), reference_name

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

		rows = self.activities
		if rows and all(is_finished(row) for row in rows):
			self.boarding_status = "Completed"
		elif any(row.completed or row.status for row in rows):
			self.boarding_status = "In Process"
		else:
			self.boarding_status = "Pending"

	def sync_todos(self):
		"""Give every open, assigned row a ToDo of its own, and close those of finished rows."""
		if self.is_new():
			return

		for row in self.activities:
			if row.todo and (is_finished(row) or not row.user):
				close_todo(row.todo, "Closed" if is_finished(row) else "Cancelled")
				row.db_set("todo", None)
			elif row.user and not row.todo and not is_finished(row):
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
		self.finish_activity(activity, completed=1)

	@frappe.whitelist(methods=["POST"])
	def skip_activity(self, row: str) -> None:
		self.check_permission("write")
		self.finish_activity(self.get_activity(row), skipped=1)

	@frappe.whitelist(methods=["POST"])
	def unskip_activity(self, row: str) -> None:
		self.check_permission("write")
		self.get_activity(row).db_set("skipped", 0)
		self.save_activity_states()

	@frappe.whitelist(methods=["POST"])
	def set_activity_progress(self, row: str, status: str | None = None) -> None:
		"""Mark an unfinished activity In Progress or Stuck, or clear that; finishing is by record."""
		self.check_permission("write")
		activity = self.get_activity(row)
		if status and status not in PROGRESS_STATUSES:
			frappe.throw(_("Status must be In Progress or Stuck"))
		if is_finished(activity):
			frappe.throw(_("{0} is already finished").format(activity.activity_name))
		activity.db_set("status", status or None)
		self.save_activity_states()

	@frappe.whitelist(methods=["POST"])
	def sync_activities(self) -> None:
		self.check_permission("write")
		self.save_activity_states()

	def finish_activity(self, activity, completed: int = 0, skipped: int = 0):
		activity.db_set({"completed": completed, "skipped": skipped, "status": None})
		self.save_activity_states()

	def complete_remaining_activities(self):
		for row in self.activities:
			if not is_finished(row):
				row.completed = int(row.action == "Manual")
				row.skipped = int(row.action != "Manual")
				row.status = None
		self.boarding_status = "Completed"


def is_finished(row) -> bool:
	return bool(row.completed or row.skipped)


def close_todo(name: str, status: str) -> None:
	todo = frappe.get_doc("ToDo", name)
	if todo.status != "Open":
		return
	todo.status = status
	todo.save(ignore_permissions=True)
	if status == "Cancelled":
		notify_assignment(todo.assigned_by, todo.allocated_to, todo.reference_type, todo.reference_name)


def get_matching_template(doc) -> str | None:
	"""The newest template whose company, department, designation and grade each match the
	onboarding's or are left blank, so a blank template applies to everyone."""
	Template = frappe.qb.DocType("Employee Onboarding Template")
	query = frappe.qb.from_(Template).select(Template.name).orderby(Template.creation, order=Order.desc)
	for field in TEMPLATE_MATCH_FIELDS:
		is_blank = IfNull(Template[field], "") == ""
		value = doc.get(field)
		query = query.where(is_blank | (Template[field] == value) if value else is_blank)
	templates = query.limit(1).run(pluck=True)
	return templates[0] if templates else None


def get_template_activities(template: str | None) -> list[dict]:
	if not template:
		return []
	return frappe.get_all(
		"Employee Boarding Activity",
		fields=TEMPLATE_ROW_FIELDS,
		filters={"parent": template, "parenttype": "Employee Onboarding Template"},
		order_by="idx",
	)


def set_action_defaults(row) -> None:
	row.action = row.action or "Manual"
	if row.action in ACTION_DOCTYPES:
		row.reference_doctype = ACTION_DOCTYPES[row.action]
	elif row.action == "Manual":
		row.reference_doctype = None


def validate_unique_actions(rows, where: str) -> None:
	seen = set()
	for row in rows:
		if row.action == "Manual":
			continue
		key = action_key(row.action, row.reference_doctype)
		if key in seen:
			frappe.throw(_("Row #{0}: {1} is already on {2}").format(row.idx, _(row.activity_name), where))
		seen.add(key)


def action_key(action: str | None, reference_doctype: str | None) -> tuple:
	return action, ACTION_DOCTYPES.get(action) or reference_doctype


def add_standard_activities(template) -> None:
	"""Put the standard activities at the top of a new template; it may drop them later."""
	present = {action_key(row.action, row.reference_doctype) for row in template.activities}
	own_rows = list(template.activities)
	template.activities = []
	for activity in STANDARD_ACTIVITIES:
		if action_key(activity["action"], activity.get("reference_doctype")) not in present:
			template.append("activities", activity)
	for row in own_rows:
		template.append("activities", row)
	for idx, row in enumerate(template.activities, start=1):
		row.idx = idx
