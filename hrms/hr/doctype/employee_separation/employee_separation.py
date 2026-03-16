# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from hrms.controllers.employee_boarding_controller import EmployeeBoardingController


class EmployeeSeparation(EmployeeBoardingController):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_boarding_activity.employee_boarding_activity import (
			EmployeeBoardingActivity,
		)

		activities: DF.Table[EmployeeBoardingActivity]
		amended_from: DF.Link | None
		boarding_begins_on: DF.Date
		boarding_status: DF.Literal["Pending", "In Process", "Completed"]
		company: DF.Link
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link
		employee_grade: DF.Link | None
		employee_name: DF.Data | None
		employee_separation_template: DF.Link | None
		exit_interview: DF.TextEditor | None
		notify_users_by_email: DF.Check
		project: DF.Link | None
		resignation_letter_date: DF.Date | None
	# end: auto-generated types

	def validate(self):
		super().validate()

	def on_submit(self):
		super().on_submit()

	def on_update_after_submit(self):
		self.create_task_and_notify_user()

	def on_cancel(self):
		super().on_cancel()
