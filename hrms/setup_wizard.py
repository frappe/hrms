import frappe
from frappe import _
from frappe.utils.telemetry import capture


def get_setup_stages(wizard_args=None):
	if not frappe.conf.sk_hrms:
		return []

	return [
		{
			"status": _("Personalizing your setup"),
			"fail_msg": _("Failed to personalize your setup"),
			"tasks": [
				{
					"fn": capture_user_persona,
					"args": persona_from_wizard_args(wizard_args) if wizard_args else None,
					"fail_msg": _("Failed to personalize your setup"),
				}
			],
		}
	]


# The exact property set of the `user_persona_submitted` event. The wizard
# runner mutates task args on resumed setups (`set_missing_values`), so the
# event is pinned to these fields instead of whatever the payload accumulates.
PERSONA_FIELDS = (
	"implementing_for",
	"company_size",
	"industry",
	"current_system",
	"module_leave_attendance",
	"module_payroll",
	"module_recruitment",
	"module_performance",
	"country",
	"language",
)


def persona_from_wizard_args(wizard_args: dict) -> dict:
	"""Narrow the raw wizard payload to the fields the persona event reports."""
	return {
		"implementing_for": wizard_args.get("persona_implementing_for"),
		"company_size": wizard_args.get("persona_company_size"),
		"industry": wizard_args.get("persona_industry"),
		"current_system": wizard_args.get("persona_current_system"),
		"module_leave_attendance": bool(wizard_args.get("module_leave_attendance")),
		"module_payroll": bool(wizard_args.get("module_payroll")),
		"module_recruitment": bool(wizard_args.get("module_recruitment")),
		"module_performance": bool(wizard_args.get("module_performance")),
		"country": wizard_args.get("country"),
		"language": wizard_args.get("language"),
	}


def capture_user_persona(persona: dict | None):
	"""Send the persona answers captured on the setup slide to telemetry.

	The wizard runner calls every task as ``fn(task["args"])``, so this takes the
	narrowed payload from ``persona_from_wizard_args``, never the raw wizard args.
	"""
	if not persona:
		return

	capture(
		"user_persona_submitted",
		"hrms",
		properties={field: persona.get(field) for field in PERSONA_FIELDS},
	)
