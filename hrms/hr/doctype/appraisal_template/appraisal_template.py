# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from hrms.mixins.appraisal import AppraisalMixin


class AppraisalTemplate(Document, AppraisalMixin):
	def validate(self):
		self.validate_total_weightage("goals", "KRAs")
		self.validate_total_weightage("rating_criteria", "Criteria")
