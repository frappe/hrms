import frappe
from frappe import _
from frappe.utils import flt


class AppraisalMixin:
	"""Mixin class for common validations in Appraisal doctypes"""

	def validate_total_weightage(self, table_name: str, table_label: str) -> None:
		if not self.get(table_name):
			return

		total_weightage = sum(flt(d.per_weightage) for d in self.get(table_name))

		if flt(total_weightage, 2) != 100.0:
			frappe.throw(
				_("Total weightage for all {0} must add up to 100. Currently, it is {1}%").format(
					frappe.bold(_(table_label)), total_weightage
				),
				title=_("Incorrect Weightage Allocation"),
			)
