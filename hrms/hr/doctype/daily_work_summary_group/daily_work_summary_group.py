# # Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt


import frappe
import frappe.utils
from frappe import _
from frappe.model.document import Document

from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

from hrms.hr.doctype.daily_work_summary.daily_work_summary import get_user_emails_from_group


class DailyWorkSummaryGroup(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.daily_work_summary_group_user.daily_work_summary_group_user import (
			DailyWorkSummaryGroupUser,
		)

		enabled: DF.Check
		holiday_list: DF.Link | None
		message: DF.TextEditor | None
		send_emails_at: DF.Literal[
			"00:00",
			"01:00",
			"02:00",
			"03:00",
			"04:00",
			"05:00",
			"06:00",
			"07:00",
			"08:00",
			"09:00",
			"10:00",
			"11:00",
			"12:00",
			"13:00",
			"14:00",
			"15:00",
			"16:00",
			"17:00",
			"18:00",
			"19:00",
			"20:00",
			"21:00",
			"22:00",
			"23:00",
		]
		subject: DF.Data | None
		users: DF.Table[DailyWorkSummaryGroupUser]
	# end: auto-generated types

	def validate(self):
		if self.users:
			if not frappe.flags.in_test and not is_incoming_account_enabled():
				frappe.throw(
					_("Please enable default incoming account before creating Daily Work Summary Group")
				)


def trigger_emails():
	"""Send emails to Employees at the given hour asking
	them what did they work on today"""
	groups = frappe.get_all("Daily Work Summary Group")
	for d in groups:
		group_doc = frappe.get_doc("Daily Work Summary Group", d)
		if (
			is_current_hour(group_doc.send_emails_at)
			and not is_holiday(group_doc.holiday_list)
			and group_doc.enabled
		):
			emails = get_user_emails_from_group(group_doc)
			# find emails relating to a company
			if emails:
				daily_work_summary = frappe.get_doc(
					dict(doctype="Daily Work Summary", daily_work_summary_group=group_doc.name)
				).insert()
				daily_work_summary.send_mails(group_doc, emails)


def is_current_hour(hour):
	return frappe.utils.nowtime().split(":")[0] == hour.split(":")[0]


def send_summary():
	"""Send summary to everyone"""
	for d in frappe.get_all("Daily Work Summary", dict(status="Open")):
		daily_work_summary = frappe.get_doc("Daily Work Summary", d.name)
		daily_work_summary.send_summary()


def is_incoming_account_enabled():
	return frappe.db.get_value("Email Account", dict(enable_incoming=1, default_incoming=1))
