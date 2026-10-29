import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils.telemetry import capture

from hrms.subscription_utils import is_new_hr_site, set_hrms_as_default_app


def get_setup_stages(wizard_args=None):
	stages = [
		{
			"status": _("Creating your holiday list"),
			"fail_msg": _("Failed to create your holiday list"),
			"tasks": [
				{
					"fn": create_default_holiday_list,
					"args": holiday_list_from_wizard_args(wizard_args) if wizard_args else None,
					"fail_msg": _("Failed to create your holiday list"),
				}
			],
		}
	]

	if not frappe.conf.sk_hrms:
		return stages

	tasks = [
		{
			"fn": capture_user_persona,
			"args": persona_from_wizard_args(wizard_args) if wizard_args else None,
			"fail_msg": _("Failed to personalize your setup"),
		}
	]

	# frappe's own stage marks it complete before this task runs, so decide while building stages
	if is_new_hr_site():
		tasks.append(
			{
				"fn": set_hrms_as_default_app,
				"args": None,
				"fail_msg": _("Failed to personalize your setup"),
			}
		)

	stages.append(
		{
			"status": _("Personalizing your setup"),
			"fail_msg": _("Failed to personalize your setup"),
			"tasks": tasks,
		}
	)
	return stages


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


WEEKLY_OFFS_BY_COUNTRY = {
	"AE": ("Saturday", "Sunday"),
	"BH": ("Friday", "Saturday"),
	"EG": ("Friday", "Saturday"),
	"IL": ("Friday", "Saturday"),
	"IR": ("Friday",),
	"JO": ("Friday", "Saturday"),
	"KW": ("Friday", "Saturday"),
	"OM": ("Friday", "Saturday"),
	"QA": ("Friday", "Saturday"),
	"SA": ("Friday", "Saturday"),
}


def holiday_list_from_wizard_args(wizard_args: dict) -> dict:
	"""Narrow the raw wizard payload to the fields the default holiday list needs."""
	return {
		"company": wizard_args.get("company_name"),
		"country": wizard_args.get("country"),
		"from_date": wizard_args.get("fy_start_date"),
		"to_date": wizard_args.get("fy_end_date"),
	}


def create_default_holiday_list(args: dict | None):
	"""Create the company's default holiday list for its first fiscal year, never failing the setup."""
	if not args or not args.get("company") or not frappe.db.exists("Company", args.get("company")):
		return

	if frappe.db.get_value("Company", args.get("company"), "default_holiday_list"):
		return

	frappe.db.savepoint("default_holiday_list")
	try:
		holiday_list = make_holiday_list(args)
		frappe.db.set_value("Company", args.get("company"), "default_holiday_list", holiday_list.name)
	except Exception:
		frappe.db.rollback(save_point="default_holiday_list")
		frappe.log_error(title="Failed to create the default holiday list")


def make_holiday_list(args: dict):
	from_date = getdate(args.get("from_date") or f"{getdate().year}-01-01")
	to_date = getdate(args.get("to_date") or f"{from_date.year}-12-31")
	year = str(from_date.year) if from_date.year == to_date.year else f"{from_date.year}-{to_date.year}"
	name = f"{args.get('company')} {year}"

	if frappe.db.exists("Holiday List", name):
		return frappe.get_doc("Holiday List", name)

	holiday_list = frappe.new_doc("Holiday List")
	holiday_list.holiday_list_name = name
	holiday_list.from_date = from_date
	holiday_list.to_date = to_date

	country_code = get_country_code(args.get("country"))
	if is_supported_by_holidays_library(country_code):
		holiday_list.country = country_code
		holiday_list.get_local_holidays()

	# after public holidays, so a holiday on a weekend keeps its name instead of the weekday's
	for weekly_off in WEEKLY_OFFS_BY_COUNTRY.get(country_code, ("Sunday",)):
		holiday_list.weekly_off = weekly_off
		holiday_list.get_weekly_off_dates()

	holiday_list.insert()
	return holiday_list


def get_country_code(country: str | None) -> str | None:
	if not country:
		return None

	code = frappe.db.get_value("Country", country, "code")
	return code.upper() if code else None


def is_supported_by_holidays_library(country_code: str | None) -> bool:
	from holidays.utils import list_supported_countries

	return bool(country_code) and country_code in list_supported_countries()
