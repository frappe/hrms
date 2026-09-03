import frappe
from frappe import _
from frappe.utils.telemetry import capture


def get_setup_stages(args=None):
	if not frappe.conf.sk_hrms:
		return []

	return [
		{
			"status": _("Personalizing your setup"),
			"fail_msg": _("Failed to personalize your setup"),
			"tasks": [
				{"fn": capture_user_persona, "args": args, "fail_msg": _("Failed to personalize your setup")}
			],
		}
	]


def capture_user_persona(args):
	"""Send the persona answers captured on the setup slide to telemetry."""
	if not args:
		return

	capture(
		"user_persona_submitted",
		"hrms",
		properties={
			"implementing_for": args.get("persona_implementing_for"),
			"company_size": args.get("persona_company_size"),
			"industry": args.get("persona_industry"),
			"current_system": args.get("persona_current_system"),
			"module_leave_attendance": bool(args.get("module_leave_attendance")),
			"module_payroll": bool(args.get("module_payroll")),
			"module_recruitment": bool(args.get("module_recruitment")),
			"module_performance": bool(args.get("module_performance")),
			"country": args.get("country"),
			"language": args.get("language"),
		},
	)
