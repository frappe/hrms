import re

import frappe
from frappe.email.doctype.notification.notification import clear_notification_cache
from frappe.utils import cint
from frappe.utils.html_utils import sanitize_html

# Pre-refactor default content, used to detect if a site customized it.
ORIGINAL_EMAIL_CONTENT = """<h1>Leave Application Notification</h1>
<h3>Details:</h3>

	<table class="table table-bordered small" style="max-width: 500px;">
		<tr>
			<td>Employee</td>
			<td>{{employee_name}}</td>
		</tr>
		<tr>
			<td>Leave Type</td>
			<td>{{leave_type}}</td>
		</tr>
		<tr>
			<td>From Date</td>
			<td>{{from_date}}</td>
		</tr>
		<tr>
			<td>To Date</td>
			<td>{{to_date}}</td>
		</tr>
		<tr>
			<td>Status</td>
			<td>{{status}}</td>
		</tr>
	</table>

	{% set doc_link = frappe.utils.get_url_to_form('Leave Application', name) %}

	<br><br>
	<a class="btn btn-primary" href="{{ doc_link }}" target="_blank">{{ _('Open Now') }}</a>"""

OLD_DEFAULT_TEMPLATES = ("Leave Approval Notification", "Leave Status Notification")

NOTIFICATION_TO_OLD_SETTING = {
	"Leave Application Pending Approval": "leave_approval_notification_template",
	"Leave Application Status Update": "leave_status_notification_template",
	"Leave Application Cancelled": "leave_status_notification_template",
}


def execute():
	"""Preserve customized Leave Application notification content after the refactor to a shared Email Template."""
	if not frappe.db.exists("Notification", "Leave Application Pending Approval"):
		return

	raw_send_leave_notification = get_old_single_value("send_leave_notification")
	# "1" was the field's default, so a never-touched site behaves as still on.
	send_leave_notification = (
		cint(raw_send_leave_notification) if raw_send_leave_notification is not None else 1
	)

	for notification_name, setting_field in NOTIFICATION_TO_OLD_SETTING.items():
		if not frappe.db.exists("Notification", notification_name):
			continue

		template_name = get_old_single_value(setting_field)
		if is_customized(template_name):
			clone_with_custom_template(notification_name, template_name, bool(send_leave_notification))
		elif not send_leave_notification:
			frappe.db.set_value("Notification", notification_name, "enabled", 0)

	delete_unused_default_templates()
	# db.set_value() above skips Notification.clear_cache(), so the cache goes stale.
	clear_notification_cache()


def get_old_single_value(fieldname):
	# get_single_value() throws once this field leaves hr_settings.json; read Singles directly.
	return frappe.db.get_value(
		"Singles", {"doctype": "HR Settings", "field": fieldname}, "value", order_by=None
	)


def is_customized(template_name):
	if not template_name or not frappe.db.exists("Email Template", template_name):
		return False

	# sanitize_html() alters saved content (adds <tbody>, rel="noopener"...) but not inter-tag
	# whitespace, so sanitize both sides then normalize whitespace too before comparing.
	response = frappe.db.get_value("Email Template", template_name, "response") or ""
	canonical_original = sanitize_html(ORIGINAL_EMAIL_CONTENT, linkify=True)
	return normalize(response) != normalize(canonical_original)


def normalize(html):
	html = re.sub(r">\s+<", "><", html)
	html = re.sub(r"\s+", " ", html)
	return html.strip()


def clone_with_custom_template(notification_name, template_name, enabled):
	custom_name = f"{notification_name} (Custom)"
	if frappe.db.exists("Notification", custom_name):
		return

	clone = frappe.copy_doc(frappe.get_doc("Notification", notification_name))
	clone.name = custom_name
	clone.is_standard = 0
	clone.email_template = template_name
	clone.enabled = 1 if enabled else 0
	clone.insert(ignore_permissions=True)

	frappe.db.set_value("Notification", notification_name, "enabled", 0)


def delete_unused_default_templates():
	for template_name in OLD_DEFAULT_TEMPLATES:
		if not frappe.db.exists("Email Template", template_name):
			continue
		if is_customized(template_name):
			continue
		try:
			frappe.delete_doc("Email Template", template_name, ignore_permissions=True)
		except frappe.LinkExistsError:
			pass
