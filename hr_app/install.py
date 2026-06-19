import frappe


def after_install():
	create_hr_settings_custom_fields()


def create_hr_settings_custom_fields():
	fields = [
		{
			"dt": "HR Settings",
			"fieldname": "require_checkin_photo",
			"fieldtype": "Check",
			"label": "Require Checkin Photo",
			"description": "If enabled, employees must capture a photo when checking in via the mobile app.",
			"default": "0",
			"insert_after": "allow_geolocation_tracking",
		},
		{
			"dt": "HR Settings",
			"fieldname": "hide_accounting_features",
			"fieldtype": "Check",
			"label": "Hide Accounting Features",
			"description": "If enabled, expense claims and employee advances are hidden in the mobile app.",
			"default": "1",
			"insert_after": "require_checkin_photo",
		},
		{
			"dt": "HR Settings",
			"fieldname": "enable_live_tracking",
			"fieldtype": "Check",
			"label": "Enable Live Location Tracking",
			"description": "If enabled, the mobile app tracks an employee's location while they are checked in.",
			"default": "0",
			"insert_after": "hide_accounting_features",
		},
		{
			"dt": "HR Settings",
			"fieldname": "tracking_interval",
			"fieldtype": "Int",
			"label": "Location Tracking Interval (seconds)",
			"description": "How often the mobile app records a location ping while tracking is active.",
			"default": "60",
			"insert_after": "enable_live_tracking",
		},
	]

	for field in fields:
		if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
			frappe.get_doc({"doctype": "Custom Field", **field}).insert()
