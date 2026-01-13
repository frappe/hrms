# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Count
from frappe.query_builder.terms import SubQuery


class AppraisalCycle(Document):
	def onload(self):
		self.set_onload("appraisals_created", self.check_if_appraisals_exist())

	def validate(self):
		self.validate_from_to_dates("start_date", "end_date")
		self.validate_evaluation_method_change()

	def validate_evaluation_method_change(self):
		if self.is_new():
			return

		if self.has_value_changed("kra_evaluation_method") and self.check_if_appraisals_exist():
			frappe.throw(
				_(
					"Evaluation Method cannot be changed as there are existing appraisals created for this cycle"
				),
				title=_("Not Allowed"),
			)

	def check_if_appraisals_exist(self):
		return frappe.db.exists(
			"Appraisal",
			{"appraisal_cycle": self.name, "docstatus": ["!=", 2]},
		)

	@frappe.whitelist()
	def set_employees(self):
		"""Pull employees in appraisee list based on selected filters"""
		employees = self.get_employees_for_appraisal()
		appraisal_templates = self.get_appraisal_template_map()

		if employees:
			self.set("appraisees", [])
			template_missing = False

			for data in employees:
				if not appraisal_templates.get(data.designation):
					template_missing = True

				self.append(
					"appraisees",
					{
						"employee": data.name,
						"employee_name": data.employee_name,
						"branch": data.branch,
						"designation": data.designation,
						"department": data.department,
						"appraisal_template": appraisal_templates.get(data.designation),
					},
				)

			if template_missing:
				self.show_missing_template_message()
		else:
			self.set("appraisees", [])
			frappe.msgprint(_("No employees found for the selected criteria"))

		return self

	def get_employees_for_appraisal(self):
		filters = {
			"status": "Active",
			"company": self.company,
		}
		if self.department:
			filters["department"] = self.department
		if self.branch:
			filters["branch"] = self.branch
		if self.designation:
			filters["designation"] = self.designation

		employees = frappe.db.get_all(
			"Employee",
			filters=filters,
			fields=[
				"name",
				"employee_name",
				"branch",
				"designation",
				"department",
			],
		)

		return employees

	def get_appraisal_template_map(self):
		designations = frappe.get_all("Designation", fields=["name", "appraisal_template"])
		appraisal_templates = frappe._dict()

		for entry in designations:
			appraisal_templates[entry.name] = entry.appraisal_template

		return appraisal_templates

	@frappe.whitelist()
	def create_appraisals(self):
		self.check_permission("write")
		if not self.appraisees:
			frappe.throw(
				_("Please select employees to create appraisals for"), title=_("No Employees Selected")
			)

		if not all(appraisee.appraisal_template for appraisee in self.appraisees):
			self.show_missing_template_message(raise_exception=True)

		if len(self.appraisees) > 30:
			frappe.enqueue(
				create_appraisals_for_cycle,
				queue="long",
				timeout=600,
				appraisal_cycle=self,
			)
			frappe.msgprint(
				_("Appraisal creation is queued. It may take a few minutes."),
				alert=True,
				indicator="blue",
			)
		else:
			create_appraisals_for_cycle(self, publish_progress=True)
			# since this method is called via frm.call this doc needs to be updated manually
			self.reload()

	def show_missing_template_message(self, raise_exception=False):
		msg = _("Appraisal Template not found for some designations.")
		msg += "<br><br>"
		msg += _(
			"Please set the Appraisal Template for all the {0} or select the template in the Employees table below."
		).format(f"""<a href='{frappe.utils.get_url_to_list("Designation")}'>Designations</a>""")

		frappe.msgprint(
			msg, title=_("Appraisal Template Missing"), indicator="yellow", raise_exception=raise_exception
		)

	@frappe.whitelist()
	def complete_cycle(self):
		self.check_permission("write")

		draft_appraisals = frappe.db.count("Appraisal", {"appraisal_cycle": self.name, "docstatus": 0})

		if draft_appraisals:
			link = frappe.utils.get_url_to_list("Appraisal") + f"?status=Draft&appraisal_cycle={self.name}"
			link = f"""<a href="{link}">documents</a>"""

			msg = _("{0} Appraisal(s) are not submitted yet").format(frappe.bold(draft_appraisals))
			msg += "<br><br>"
			msg += _("Please submit the {0} before marking the cycle as Completed").format(link)
			frappe.throw(msg, title=_("Unsubmitted Appraisals"))

		self.status = "Completed"
		self.save()


def create_appraisals_for_cycle(appraisal_cycle: AppraisalCycle, publish_progress: bool = False):
	"""
	Creates appraisals for employees in the appraisee list of appraisal cycle,
	if not already created
	"""
	count = 0

	for employee in appraisal_cycle.appraisees:
		try:
			appraisal = frappe.get_doc(
				{
					"doctype": "Appraisal",
					"company": appraisal_cycle.company,
					"appraisal_template": employee.appraisal_template,
					"employee": employee.employee,
					"appraisal_cycle": appraisal_cycle.name,
				}
			)

			appraisal.rate_goals_manually = (
				1 if appraisal_cycle.kra_evaluation_method == "Manual Rating" else 0
			)
			appraisal.set_kras_and_rating_criteria()
			appraisal.insert()

			if publish_progress:
				count += 1
				frappe.publish_progress(
					count * 100 / len(appraisal_cycle.appraisees), title=_("Creating Appraisals") + "..."
				)
		except frappe.DuplicateEntryError:
			# already exists
			pass


def validate_active_appraisal_cycle(appraisal_cycle: str) -> None:
	if frappe.db.get_value("Appraisal Cycle", appraisal_cycle, "status") == "Completed":
		msg = _("Cannot create or change transactions against an Appraisal Cycle with status {0}.").format(
			frappe.bold(_("Completed"))
		)
		msg += "<br><br>"
		msg += _("Set the status to {0} if required.").format(frappe.bold(_("In Progress")))

		frappe.throw(msg, title=_("Not Allowed"))


@frappe.whitelist()
def get_appraisal_cycle_summary(cycle_name: str) -> dict:
	summary = frappe._dict()

	summary["appraisees"] = frappe.db.count(
		"Appraisal", {"appraisal_cycle": cycle_name, "docstatus": ("!=", 2)}
	)
	summary["self_appraisal_pending"] = frappe.db.count(
		"Appraisal", {"appraisal_cycle": cycle_name, "docstatus": 0, "self_score": 0}
	)
	summary["goals_missing"] = get_employees_without_goals(cycle_name)
	summary["feedback_missing"] = get_employees_without_feedback(cycle_name)

	return summary


def get_employees_without_goals(cycle_name: str) -> int:
	Goal = frappe.qb.DocType("Goal")
	Appraisal = frappe.qb.DocType("Appraisal")
	count = Count("*").as_("count")

	filtered_records = SubQuery(
		frappe.qb.from_(Goal)
		.select(Goal.employee)
		.distinct()
		.where((Goal.appraisal_cycle == cycle_name) & (Goal.status != "Archived"))
	)

	goals_missing = (
		frappe.qb.from_(Appraisal)
		.select(count)
		.where(
			(Appraisal.appraisal_cycle == cycle_name)
			& (Appraisal.docstatus != 2)
			& (Appraisal.employee.notin(filtered_records))
		)
	).run(as_dict=True)

	return goals_missing[0].count


@frappe.whitelist()
def get_employees_without_feedback(cycle_name: str | None = None) -> int:
	Feedback = frappe.qb.DocType("Employee Performance Feedback")
	Appraisal = frappe.qb.DocType("Appraisal")
	count = Count("*").as_("count")
	if not cycle_name:
		cycle_name = frappe.get_value(
			"Appraisal Cycle", {"status": "In Progress"}, order_by="start_date desc"
		)

	filtered_records = SubQuery(
		frappe.qb.from_(Feedback)
		.select(Feedback.employee)
		.distinct()
		.where((Feedback.appraisal_cycle == cycle_name) & (Feedback.docstatus == 1))
	)

	feedback_missing = (
		frappe.qb.from_(Appraisal)
		.select(count)
		.where(
			(Appraisal.appraisal_cycle == cycle_name)
			& (Appraisal.docstatus != 2)
			& (Appraisal.employee.notin(filtered_records))
		)
	).run(as_dict=True)

	return feedback_missing[0].count
