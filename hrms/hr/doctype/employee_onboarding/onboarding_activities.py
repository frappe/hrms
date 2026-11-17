# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from pypika.terms import ExistsCriterion

import frappe
from frappe import _
from frappe.desk.form.assign_to import notify_assignment
from frappe.permissions import AUTOMATIC_ROLES
from frappe.query_builder import Order
from frappe.query_builder.functions import IfNull
from frappe.utils import add_days, get_link_to_form

from hrms.hr.doctype.employee_request.employee_request import PREBOARDING_CANDIDATE_ROLE

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
	"Set Roles": "User",
}

PROGRESS_STATUSES = ("In Progress", "Stuck")

EMPLOYEE_SELF_SERVICE_ROLE = "Employee Self Service"
ONBOARDING_ROLES = ("Employee", EMPLOYEE_SELF_SERVICE_ROLE, PREBOARDING_CANDIDATE_ROLE)

TEMPLATE_MATCH_FIELDS = ("company", "department", "designation", "employee_grade")

TEMPLATE_ROW_FIELDS = [
	"activity_name",
	"action",
	"reference_doctype",
	"depends_on_action",
	"required_for_employee_creation",
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
	{"activity_name": "Create User Login", "action": "Create User"},
	{"activity_name": "Create Employee", "action": "Create Employee"},
	{
		"activity_name": "Set Roles and Permissions",
		"action": "Set Roles",
		"depends_on_action": "Create Employee",
	},
	make_assign_activity("Assign Holiday List", "Holiday List Assignment"),
	make_assign_activity("Assign Leave Policy", "Leave Policy Assignment"),
	make_assign_activity("Assign Salary Structure", "Salary Structure Assignment"),
	make_assign_activity("Assign Shift Type", "Shift Assignment"),
	{
		"activity_name": "Send Appointment Letter",
		"action": "Appointment Letter",
		"depends_on_action": "Create Employee",
	},
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
		if not self.employee_boarding_template:
			self.employee_boarding_template = get_matching_template(self)
		if self.employee_boarding_template:
			self.notify_users_by_email = frappe.db.get_value(
				"Employee Boarding Template", self.employee_boarding_template, "notify_users_by_email"
			)

	def set_activities(self):
		if not self.activities:
			for row in get_template_activities(self.employee_boarding_template):
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

	def validate_employee_creation(self):
		pending = [
			frappe.bold(_(row.activity_name))
			for row in self.activities
			if is_pending_for_employee_creation(row)
		]
		if pending:
			frappe.throw(
				_("Complete or skip {0} on onboarding {1} before creating the employee").format(
					", ".join(pending), get_link_to_form(self.doctype, self.name)
				),
				title=_("Onboarding Activities Pending"),
			)

	def get_lock_reasons(self) -> dict[str, list[str]]:
		"""The names of the unfinished activities each row waits for, by row."""
		return {
			row.name: needed
			for row in self.activities
			if (needed := [other.activity_name for other in self.activities if is_needed_by(row, other)])
		}

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
				done = bool(self.appointment_letter_sent_on)
			case "Create Employee":
				reference_name = self.employee
				done = bool(self.employee)
			case "Set Roles":
				done = bool(self.roles_set_on or has_assigned_access(self.user))
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
		self.update_boarding_status()
		self.sync_todos()
		self.set_onload("lock_reasons", self.get_lock_reasons())

	def publish_change(self):
		self.update_modified()
		self.notify_update()

	def get_draft_assignments(self) -> dict:
		if not self.employee:
			return {}

		drafts = {}
		for doctype, config in ASSIGNMENTS.items():
			filters = {config["employee_field"]: self.employee, "docstatus": 0, **config.get("filters", {})}
			if frappe.get_meta(doctype).is_submittable and (draft := frappe.db.get_value(doctype, filters)):
				drafts[doctype] = draft
		return drafts

	def get_assignee_info(self) -> dict:
		user_info = {}
		frappe.utils.add_user_info({row.user for row in self.activities if row.user}, user_info)
		return user_info

	def set_boarding_status(self):
		if self.docstatus == 2:
			return

		if self.docstatus == 0:
			self.boarding_status = "Pending"
		elif all(is_finished(row) for row in self.activities):
			self.boarding_status = "Completed"
		else:
			self.boarding_status = self.get_preboarding_status() or "In Process"

	def get_preboarding_status(self) -> str | None:
		if not self.user or self.employee:
			return None
		request = frappe.db.get_value(
			"Employee Request", {"employee_onboarding": self.name}, ["name", "submitted_on"], as_dict=True
		)
		if not request:
			return None
		return "Details Submitted" if request.submitted_on else "Awaiting Employee Details"

	def update_boarding_status(self):
		self.set_boarding_status()
		self.db_set("boarding_status", self.boarding_status, notify=True)

	def sync_todos(self):
		"""Give every open, assigned row a ToDo of its own, and close those of finished rows."""
		if self.docstatus != 1:
			return

		for row in self.activities:
			if row.todo and (is_finished(row) or not row.user):
				self.close_todo(row.todo, "Closed" if is_finished(row) else "Cancelled")
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
		if self.notify_users_by_email:
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
		self.validate_draft()
		self.get_activity(row).db_set("user", user or None)
		self.publish_change()

	@frappe.whitelist(methods=["POST"])
	def set_activity_due_date(self, row: str, due_date: str | None = None) -> None:
		self.check_permission("write")
		self.validate_draft()
		self.get_activity(row).db_set("due_date", due_date or None)
		self.publish_change()

	@frappe.whitelist(methods=["POST"])
	def add_activity(self, activity_name: str) -> None:
		self.check_permission("write")
		self.validate_draft()
		activity_name = self.validate_new_activity_name(activity_name)
		activity = self.append("activities", {"activity_name": activity_name, "added_on_onboarding": 1})
		self.set_activity_defaults(activity)
		activity.db_insert()
		self.save_activity_states()

	@frappe.whitelist(methods=["POST"])
	def remove_activity(self, row: str) -> None:
		self.check_permission("write")
		self.validate_draft()
		activity = self.get_activity(row)
		if not activity.added_on_onboarding:
			frappe.throw(_("Only activities added on this onboarding can be removed; skip the others"))

		self.remove(activity)
		frappe.db.delete(activity.doctype, activity.name)
		for other in self.activities:
			other.db_set("idx", other.idx, update_modified=False)
		self.save_activity_states()

	@frappe.whitelist(methods=["POST"])
	def reorder_activities(self, rows: list[str] | str) -> None:
		self.check_permission("write")
		self.validate_draft()
		rows = frappe.parse_json(rows)
		if sorted(rows) != sorted(row.name for row in self.activities):
			frappe.throw(_("Pass every activity of this onboarding once to reorder them"))

		position = {name: idx for idx, name in enumerate(rows, start=1)}
		for row in self.activities:
			if row.idx != position[row.name]:
				row.db_set("idx", position[row.name], update_modified=False)
		self.activities.sort(key=lambda row: row.idx)
		self.publish_change()

	def validate_new_activity_name(self, activity_name: str) -> str:
		activity_name = " ".join(activity_name.split())
		max_length = frappe.get_meta("Employee Boarding Activity").get_field("activity_name").length or 140
		if not activity_name:
			frappe.throw(_("Enter a name for the activity"))
		if len(activity_name) > max_length:
			frappe.throw(_("Keep the activity name within {0} characters").format(max_length))
		if any(row.activity_name.casefold() == activity_name.casefold() for row in self.activities):
			frappe.throw(_("{0} is already on the checklist").format(frappe.bold(activity_name)))
		return activity_name

	def validate_draft(self):
		if self.docstatus != 0:
			frappe.throw(_("Activities can only be planned while the onboarding is a draft"))

	def validate_started(self):
		if self.docstatus != 1:
			frappe.throw(
				_("Submit the onboarding to start its activities"),
				title=_("Document submission required"),
			)

	def validate_not_cancelled(self):
		if self.docstatus == 2:
			frappe.throw(_("The onboarding is cancelled"))

	@frappe.whitelist(methods=["POST"])
	def complete_activity(self, row: str) -> None:
		self.check_permission("write")
		self.validate_started()
		activity = self.get_activity(row)
		if activity.action != "Manual":
			frappe.throw(_("{0} is completed by its own record").format(activity.activity_name))
		self.finish_activity(activity, completed=1)

	@frappe.whitelist(methods=["POST"])
	def reopen_activity(self, row: str) -> None:
		self.check_permission("write")
		self.validate_started()
		activity = self.get_activity(row)
		if activity.action != "Manual":
			frappe.throw(_("{0} is completed by its own record").format(activity.activity_name))
		activity.db_set("completed", 0)
		self.save_activity_states()

	@frappe.whitelist(methods=["POST"])
	def skip_activity(self, row: str) -> None:
		self.check_permission("write")
		self.validate_not_cancelled()
		self.finish_activity(self.get_activity(row), skipped=1)

	@frappe.whitelist(methods=["POST"])
	def unskip_activity(self, row: str) -> None:
		self.check_permission("write")
		self.validate_not_cancelled()
		self.get_activity(row).db_set("skipped", 0)
		self.save_activity_states()

	@frappe.whitelist(methods=["POST"])
	def set_activity_progress(self, row: str, status: str | None = None) -> None:
		"""Mark an unfinished activity In Progress or Stuck, or clear that; finishing is by record."""
		self.check_permission("write")
		self.validate_started()
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

	def close_todos(self):
		for row in self.activities:
			if row.todo:
				self.close_todo(row.todo, "Cancelled")
				row.db_set("todo", None)

	def close_todo(self, name: str, status: str) -> None:
		todo = frappe.get_doc("ToDo", name)
		if todo.status != "Open":
			return
		todo.status = status
		todo.save(ignore_permissions=True)
		if status == "Cancelled" and self.notify_users_by_email:
			notify_assignment(todo.assigned_by, todo.allocated_to, todo.reference_type, todo.reference_name)

	def clear_todos(self):
		for row in self.activities:
			row.todo = None


def has_assigned_access(user: str | None) -> bool:
	if not user:
		return False
	return bool(get_extra_roles(user) or get_role_profiles(user))


def get_extra_roles(user: str) -> list[str]:
	return frappe.get_all(
		"Has Role",
		{"parent": user, "parenttype": "User", "role": ["not in", [*AUTOMATIC_ROLES, *ONBOARDING_ROLES]]},
		pluck="role",
	)


def get_role_profiles(user: str) -> list[str]:
	return frappe.get_all("User Role Profile", {"parent": user, "parenttype": "User"}, pluck="role_profile")


def is_finished(row) -> bool:
	return bool(row.completed or row.skipped)


def is_pending_for_employee_creation(row) -> bool:
	return bool(row.required_for_employee_creation and not is_finished(row))


def is_needed_by(row, other) -> bool:
	if row.depends_on_action and other.action == row.depends_on_action and not other.completed:
		return True
	return row.action == "Create Employee" and is_pending_for_employee_creation(other)


def get_matching_template(doc) -> str | None:
	"""The newest template with onboarding activities whose company, department, designation
	and grade each match the onboarding's or are left blank, so a blank template applies to everyone."""
	Template = frappe.qb.DocType("Employee Boarding Template")
	Activity = frappe.qb.DocType("Employee Boarding Activity")
	has_activities = (
		frappe.qb.from_(Activity)
		.select(Activity.name)
		.where(Activity.parenttype == "Employee Boarding Template")
		.where(Activity.parentfield == "onboarding_activities")
		.where(Activity.disabled == 0)
		.where(Activity.parent == Template.name)
	)
	query = (
		frappe.qb.from_(Template)
		.select(Template.name)
		.where(ExistsCriterion(has_activities))
		.orderby(Template.creation, order=Order.desc)
	)
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
		filters={
			"parent": template,
			"parenttype": "Employee Boarding Template",
			"parentfield": "onboarding_activities",
			"disabled": 0,
		},
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


def validate_required_for_employee_creation(rows) -> None:
	for row in rows:
		if not row.required_for_employee_creation:
			continue
		if row.action == "Create Employee":
			frappe.throw(
				_("Row #{0}: {1} cannot be required for creating the employee").format(
					row.idx, _(row.activity_name)
				)
			)
		if row.depends_on_action == "Create Employee":
			frappe.throw(
				_(
					"Row #{0}: {1} needs the employee, so it cannot be required for creating the employee"
				).format(row.idx, _(row.activity_name))
			)


def action_key(action: str | None, reference_doctype: str | None) -> tuple:
	return action, ACTION_DOCTYPES.get(action) or reference_doctype


def has_standard_activities(template) -> bool:
	standard = {action_key(row["action"], row.get("reference_doctype")) for row in STANDARD_ACTIVITIES}
	return any(
		action_key(row.action, row.reference_doctype) in standard for row in template.onboarding_activities
	)


def add_standard_activities(template, disabled: int = 0) -> None:
	"""Add each missing standard activity after the standard one before it, or at the top."""
	rows = list(template.onboarding_activities)
	keys = [action_key(row.action, row.reference_doctype) for row in rows]
	position = 0
	for activity in STANDARD_ACTIVITIES:
		key = action_key(activity["action"], activity.get("reference_doctype"))
		if key in keys:
			position = keys.index(key) + 1
			continue
		rows.insert(position, {**activity, "disabled": disabled})
		keys.insert(position, key)
		position += 1

	if len(rows) == len(template.onboarding_activities):
		return
	template.onboarding_activities = []
	for row in rows:
		template.append("onboarding_activities", row)
	for idx, row in enumerate(template.onboarding_activities, start=1):
		row.idx = idx
