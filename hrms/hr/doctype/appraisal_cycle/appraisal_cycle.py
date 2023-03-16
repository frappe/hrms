# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class AppraisalCycle(Document):
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
				msg = _("Appraisal Template not found for some designations.")
				msg += "<br><br>"
				msg += _(
					"Please set the Appraisal Template for all the {0} or select the template in the Employees table below."
				).format(
					f"""<a href='{frappe.utils.get_url_to_list("Designation")}'>Designations</a>"""
				)

				frappe.msgprint(msg, title=_("Appraisal Template Missing"), indicator="yellow")
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
				"default_appraisal_template",
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

		if len(self.appraisees) > 30:
			frappe.enqueue(
				create_appraisals_for_cycle,
				queue="long",
				timeout=600,
				appraisal_cycle=self.name,
				employees=self.appraisees,
			)
			frappe.msgprint(
				_("Appraisal creation is queued. It may take a few minutes."),
				alert=True,
				indicator="blue",
			)
		else:
			create_appraisals_for_cycle(self.name, self.appraisees, publish_progress=True)
			# since this method is called via frm.call this doc needs to be updated manually
			self.reload()


def create_appraisals_for_cycle(appraisal_cycle, employees, publish_progress=False):
	"""
	Creates appraisals for employees in the appraisee list of appraisal cycle,
	if not already created
	"""
	count = 0

	for employee in employees:
		try:
			appraisal = frappe.get_doc(
				{
					"doctype": "Appraisal",
					"appraisal_template": employee.appraisal_template,
					"employee": employee.employee,
					"appraisal_cycle": appraisal_cycle,
				}
			)

			appraisal.set_kras()
			appraisal.insert()

			if publish_progress:
				count += 1
				frappe.publish_progress(count * 100 / len(employees), title=_("Creating Appraisals") + "...")
		except frappe.DuplicateEntryError:
			# already exists
			pass
