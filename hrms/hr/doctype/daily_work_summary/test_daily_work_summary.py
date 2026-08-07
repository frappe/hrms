# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import os

import frappe
import frappe.utils

from hrms.tests.utils import HRMSTestSuite

# test_records = frappe.get_test_records('Daily Work Summary')


class TestDailyWorkSummary(HRMSTestSuite):
	def test_email_trigger(self):
		self.setup_and_prepare_test()
		for d in self.users:
			# check that email is sent to users
			if d.message:
				self.assertTrue(
					d.email in [d.recipient for d in self.emails if self.groups.subject in d.message]
				)

	def test_email_trigger_failed(self):
		hour = "00:00"
		if frappe.utils.nowtime().split(":")[0] == "00":
			hour = "01:00"

		self.setup_and_prepare_test(hour)

		for d in self.users:
			# check that email is not sent to users
			self.assertFalse(
				d.email in [d.recipient for d in self.emails if self.groups.subject in d.message]
			)

	def test_incoming(self):
		# get test mail with message-id as in-reply-to
		self.setup_and_prepare_test()
		with open(os.path.join(os.path.dirname(__file__), "test_data", "test-reply.raw")) as f:
			if not self.emails:
				return
			test_mails = [
				f.read()
				.replace("{{ sender }}", self.users[-1].email)
				.replace("{{ message_id }}", self.emails[-1].message_id)
			]

		# pull the mail
		email_account = frappe.get_doc("Email Account", "_Test Email Account 1")
		email_account.db_set("enable_incoming", 1)
		email_account.receive(test_mails=test_mails)

		daily_work_summary = frappe.get_doc(
			"Daily Work Summary", frappe.get_all("Daily Work Summary")[0].name
		)

		args = daily_work_summary.get_message_details()

		self.assertTrue("I built Daily Work Summary!" in args.get("replies")[0].content)

	def setup_and_prepare_test(self, hour=None):
		frappe.qb.from_("Daily Work Summary").delete().run()
		frappe.qb.from_("Email Queue").delete().run()
		frappe.qb.from_("Email Queue Recipient").delete().run()
		frappe.qb.from_("Communication").delete().run()
		frappe.qb.from_("Daily Work Summary Group").delete().run()

		self.users = frappe.get_all("User", fields=["email"], filters=dict(email=("!=", "test@example.com")))
		self.setup_groups(hour)

		from hrms.hr.doctype.daily_work_summary_group.daily_work_summary_group import trigger_emails

		trigger_emails()

		# check if emails are created

		email_queue = frappe.qb.DocType("Email Queue")
		email_queue_recipient = frappe.qb.DocType("Email Queue Recipient")
		self.emails = (
			frappe.qb.from_(email_queue)
			.join(email_queue_recipient)
			.on(email_queue.name == email_queue_recipient.parent)
			.select(
				email_queue_recipient.recipient,
				email_queue.message,
				email_queue.message_id,
			)
			.run(as_dict=True)
		)

	def setup_groups(self, hour=None):
		# setup email to trigger at this hour
		if not hour:
			hour = frappe.utils.nowtime().split(":")[0]
			hour = hour + ":00"

		groups = frappe.get_doc(
			dict(
				doctype="Daily Work Summary Group",
				name="Daily Work Summary",
				users=self.users,
				send_emails_at=hour,
				subject="this is a subject for testing summary emails",
				message="this is a message for testing summary emails",
			)
		)
		groups.insert()

		self.groups = groups
		self.groups.save()
