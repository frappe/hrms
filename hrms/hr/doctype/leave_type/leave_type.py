# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import today


class LeaveType(Document):
	def validate(self):
		self.validate_lwp()
		self.validate_leave_types()
		self.validate_allocated_earned_leave()

	def validate_lwp(self):
		if self.is_lwp:
			leave_allocation = frappe.get_all(
				"Leave Allocation",
				filters={"leave_type": self.name, "from_date": ("<=", today()), "to_date": (">=", today())},
				fields=["name"],
			)
			leave_allocation = [l["name"] for l in leave_allocation]
			if leave_allocation:
				frappe.throw(
					_(
						"Leave application is linked with leave allocations {0}. Leave application cannot be set as leave without pay"
					).format(", ".join(leave_allocation))
				)  # nosec

	def validate_leave_types(self):
		if self.is_compensatory and self.is_earned_leave:
			msg = _("Leave Type can either be compensatory or earned leave.") + "<br><br>"
			msg += _("Earned Leaves are allocated as per the configured frequency via scheduler.") + "<br>"
			msg += _(
				"Whereas allocation for Compensatory Leaves is automatically created or updated on submission of Compensatory Leave Request."
			)
			msg += "<br><br>"
			msg += _("Disable {0} or {1} to proceed.").format(
				bold(_("Is Compensatory Leave")), bold(_("Is Earned Leave"))
			)
			frappe.throw(msg, title=_("Not Allowed"))

		if self.is_lwp and self.is_ppl:
			frappe.throw(_("Leave Type can either be without pay or partial pay"), title=_("Not Allowed"))

		if self.is_ppl and (
			self.fraction_of_daily_salary_per_leave < 0 or self.fraction_of_daily_salary_per_leave > 1
		):
			frappe.throw(_("The fraction of Daily Salary per Leave should be between 0 and 1"))

	def validate_allocated_earned_leave(self):
		old_configuration = self.get_doc_before_save()

		if (
			old_configuration
			and old_configuration.is_earned_leave
			and old_configuration.max_leaves_allowed > self.max_leaves_allowed
		):
			earned_leave_allocation_exists = frappe.db.exists(
				"Leave Allocation",
				{"leave_type": self.name, "from_date": ("<=", today()), "to_date": (">=", today())},
				cache=True,
			)
			if earned_leave_allocation_exists:
				frappe.msgprint(
					title=_("Leave Allocation Exists"),
					msg=_(
						"Reducing maximum leaves allowed after allocation may cause scheduler to allocate incorrect number of earned leaves. Proceed with caution."
					),
				)

	def clear_cache(self):
		from hrms.payroll.doctype.salary_slip.salary_slip import LEAVE_TYPE_MAP

		frappe.cache().delete_value(LEAVE_TYPE_MAP)
		return super().clear_cache()
