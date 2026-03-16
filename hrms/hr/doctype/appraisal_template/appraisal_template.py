# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from hrms.mixins.appraisal import AppraisalMixin


class AppraisalTemplate(Document, AppraisalMixin):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.appraisal_template_goal.appraisal_template_goal import AppraisalTemplateGoal
		from hrms.hr.doctype.employee_feedback_rating.employee_feedback_rating import EmployeeFeedbackRating

		description: DF.SmallText | None
		goals: DF.Table[AppraisalTemplateGoal]
		rating_criteria: DF.Table[EmployeeFeedbackRating]
		template_title: DF.Data
	# end: auto-generated types

	def validate(self):
		self.validate_total_weightage("goals", "KRAs")
		self.validate_total_weightage("rating_criteria", "Criteria")
