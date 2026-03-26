app_name = "hr_app"
app_title = "HortiHub HR"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "HortiHub PWA companion app for ERPNext/HRMS"
app_email = "contact@frappe.io"
app_license = "GNU General Public License (v3)"
required_apps = ["frappe/erpnext", "frappe/hrms"]

after_install = "hr_app.install.after_install"

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["dt", "in", ["HR Settings"]], ["fieldname", "in", ["require_checkin_photo", "hide_accounting_features"]]],
	}
]

website_route_rules = [
	{"from_route": "/hr-app/<path:app_path>", "to_route": "hr-app"},
	{"from_route": "/hr/<path:app_path>", "to_route": "roster"},
]
