"""Usage telemetry for HRMS.

Data policy: an event describes how a feature is used, never the person it is
used for. Properties are limited to counts, booleans, durations and values from
a fixed vocabulary. Names, free text, amounts, scores, dates and anything that
could describe an individual are stripped before the event leaves the site.
"""

import frappe
from frappe.database import savepoint
from frappe.query_builder.functions import Count
from frappe.utils import add_days, date_diff, getdate, today
from frappe.utils.telemetry import capture as _capture
from frappe.utils.telemetry import is_pulse_enabled as is_enabled
from frappe.utils.telemetry import site_age

APP = "hrms"
ACTIVATION_WINDOW_DAYS = 30

# The only string properties that may be sent, each restricted to the standard
# Select options of the field it comes from. Anything else becomes "other".
FIXED_VOCABULARIES = {
	"reason": {"Work From Home", "On Duty"},
	"log_type": {"IN", "OUT"},
	"status": {
		"Awaiting Response",
		"Accepted",
		"Rejected",
		"Cancelled",
		"Pending",
		"Under Review",
		"Cleared",
	},
	"payroll_frequency": {"Monthly", "Fortnightly", "Bimonthly", "Weekly", "Daily"},
}


def _skip_context() -> bool:
	"""Don't record telemetry from automated / non-interactive runs."""
	return bool(
		frappe.flags.in_install
		or frappe.flags.in_migrate
		or frappe.flags.in_patch
		or frappe.flags.in_test
		or frappe.flags.in_import
	)


def _should_skip() -> bool:
	return _skip_context() or not is_enabled()


def sanitize_properties(properties: dict | None) -> dict:
	clean = {}
	for key, value in (properties or {}).items():
		if value is None or isinstance(value, bool | int | float):
			clean[key] = value
		elif isinstance(value, str) and key in FIXED_VOCABULARIES:
			clean[key] = value if value in FIXED_VOCABULARIES[key] else "other"
	return clean


def capture(event: str, properties: dict | None = None) -> None:
	"""Record an HR usage event (fires on every occurrence)."""
	if _should_skip():
		return

	_capture(event, APP, properties=sanitize_properties(properties))
	_track_conversion()


MILESTONE_DOCTYPE = "HR Telemetry Milestone"


def _claim_milestone(event: str) -> bool:
	claimed = False

	with savepoint(catch=Exception):
		frappe.get_doc({"doctype": MILESTONE_DOCTYPE, "event": event}).insert(ignore_permissions=True)
		claimed = True

	return claimed


def capture_first(event: str, properties: dict | None = None) -> None:
	if _should_skip():
		return

	age = site_age()
	if not age or age > ACTIVATION_WINDOW_DAYS:
		return

	if not _claim_milestone(event):
		return

	capture(event, {"day_since_install": age, **(properties or {})})


# ---- Conversion --------------------------------------------------------------
# A site counts as converted once it is still producing usage events more than
# 14 days after its first capture. The `first_capture` milestone is pure
# bookkeeping (never sent), its creation timestamp starts the clock.

CONVERSION_WINDOW_DAYS = 14
FIRST_CAPTURE_MILESTONE = "first_capture"
CONVERSION_EVENT = "site_converted"


def _track_conversion() -> None:
	if frappe.db.exists(MILESTONE_DOCTYPE, CONVERSION_EVENT):
		return

	first_capture = frappe.db.get_value(MILESTONE_DOCTYPE, FIRST_CAPTURE_MILESTONE, "creation")
	if not first_capture:
		_claim_milestone(FIRST_CAPTURE_MILESTONE)
		return

	days_since_first_capture = date_diff(today(), first_capture)
	if days_since_first_capture <= CONVERSION_WINDOW_DAYS:
		return

	if _claim_milestone(CONVERSION_EVENT):
		_capture(
			CONVERSION_EVENT,
			APP,
			properties={
				"days_since_first_capture": days_since_first_capture,
				"day_since_install": site_age(),
			},
		)


def _duration_days(from_date, to_date) -> int | None:
	if not (from_date and to_date):
		return None
	return date_diff(to_date, from_date) + 1


LEAVE_TYPE_FLAGS = ("is_lwp", "is_ppl", "is_compensatory", "is_optional_leave", "is_earned_leave")


def on_leave_application_submit(doc, method=None):
	# The leave type's name can reveal health or family circumstances
	# (e.g. "Sick Leave"), so only its configuration flags are sent.
	flags = frappe.db.get_value("Leave Type", doc.leave_type, LEAVE_TYPE_FLAGS, as_dict=True) or {}
	capture(
		"leave_application_submitted",
		{
			**{flag: bool(flags.get(flag)) for flag in LEAVE_TYPE_FLAGS},
			"total_leave_days": doc.total_leave_days,
			"half_day": bool(doc.half_day),
			"self_approved": doc.leave_approver == frappe.session.user,
		},
	)
	capture_first("first_leave_applied")


def on_expense_claim_submit(doc, method=None):
	capture(
		"expense_claim_submitted",
		{
			"expense_count": len(doc.expenses or []),
			"is_paid": bool(doc.is_paid),
			"has_advances": bool(doc.get("advances")),
			"has_taxes": bool(doc.get("taxes")),
		},
	)
	capture_first("first_expense_claimed")


def on_attendance_request_submit(doc, method=None):
	capture(
		"attendance_request_submitted",
		{
			"reason": doc.reason,
			"half_day": bool(doc.half_day),
			"include_holidays": bool(doc.include_holidays),
			"days": _duration_days(doc.from_date, doc.to_date),
		},
	)


def on_shift_request_submit(doc, method=None):
	capture(
		"shift_request_submitted",
		{
			"has_approver": bool(doc.approver),
			"days": _duration_days(doc.from_date, doc.to_date),
		},
	)


def on_employee_checkin(doc, method=None):
	capture(
		"employee_checkin",
		{
			"log_type": doc.log_type,
			"has_shift": bool(doc.shift),
			"has_geolocation": bool(doc.latitude and doc.longitude),
			"via_device": bool(doc.device_id),
		},
	)
	capture_first("first_attendance_marked")


CREATION_MILESTONES = {
	"Employee": "first_employee_created",
	"Shift Type": "shift_type_configured",
	"Leave Type": "leave_type_configured",
	"Salary Structure": "salary_structure_created",
	"Job Opening": "recruitment_started",
	"Appraisal Cycle": "performance_cycle_started",
	"Employee Onboarding": "employee_onboarding_started",
}

# doctype -> milestone event, fired the first time such a doc is *submitted*
SUBMISSION_MILESTONES = {
	"Salary Slip": "first_salary_slip_created",
}


def on_milestone_insert(doc, method=None):
	event = CREATION_MILESTONES.get(doc.doctype)
	if event:
		capture_first(event)


def on_milestone_submit(doc, method=None):
	event = SUBMISSION_MILESTONES.get(doc.doctype)
	if event:
		capture_first(event)


# ---- Recurring completions -------------------------------------------------
# Without these the funnel goes dark after `started_creating`: payroll, offers,
# appraisals and interviews had a first-time milestone at best, so there was no
# way to tell a site that runs payroll monthly from one that ran it once.


def on_payroll_entry_submit(doc, method=None):
	capture(
		"payroll_entry_submitted",
		{
			"payroll_frequency": doc.payroll_frequency,
			"employee_count": doc.number_of_employees or len(doc.employees or []),
			"validate_attendance": bool(doc.validate_attendance),
			"based_on_timesheet": bool(doc.salary_slip_based_on_timesheet),
			"days": _duration_days(doc.start_date, doc.end_date),
		},
	)
	capture_first("first_payroll_run")


def on_job_offer_submit(doc, method=None):
	capture(
		"job_offer_made",
		{
			"status": doc.status,
			"has_terms": bool(doc.get("offer_terms")),
			"from_template": bool(doc.job_offer_term_template),
		},
	)


def on_appraisal_submit(doc, method=None):
	capture(
		"appraisal_submitted",
		{
			"has_cycle": bool(doc.appraisal_cycle),
			"goal_count": len(doc.get("goals") or []),
			"kra_count": len(doc.get("appraisal_kra") or []),
			"rated_manually": bool(doc.rate_goals_manually),
			"has_self_appraisal": bool(doc.get("self_ratings")),
		},
	)


def on_interview_submit(doc, method=None):
	capture(
		"interview_submitted",
		{
			"status": doc.status,
			"panel_size": len(doc.get("interview_details") or []),
			"from_job_opening": bool(doc.job_opening),
		},
	)


def capture_daily_attendance_pulse():
	if _should_skip():
		return

	active_employees = frappe.db.count("Employee", {"status": "Active"})
	if not active_employees:
		# Nothing set up yet — a zero-employee site would just add noise.
		return

	# The daily scheduler fires shortly after midnight, so `today` has barely
	# begun — summarising it reported ~0 check-ins and 0% participation for
	# every site. Summarise the day that just ended instead.
	day = add_days(today(), -1)
	day_start, day_end = f"{day} 00:00:00", f"{day} 23:59:59"

	checkins = frappe.db.count("Employee Checkin", {"time": ["between", [day_start, day_end]]})

	Checkin = frappe.qb.DocType("Employee Checkin")
	employees_checked_in = (
		frappe.qb.from_(Checkin)
		.select(Count(Checkin.employee).distinct())
		.where((Checkin.time >= day_start) & (Checkin.time <= day_end))
	).run()[0][0] or 0

	attendance_marked = frappe.db.count("Attendance", {"attendance_date": day, "docstatus": 1})

	def rate(n):
		return round(n / active_employees, 3)

	# Scheduler output, not usage: bypass `capture` so it never drives conversion.
	_capture(
		"attendance_daily_summary",
		APP,
		properties={
			"active_employees": active_employees,
			"checkins": checkins,
			"employees_checked_in": employees_checked_in,
			"attendance_marked": attendance_marked,
			"checkin_participation_rate": rate(employees_checked_in),
			"attendance_participation_rate": rate(attendance_marked),
			# 0 = Monday .. 6 = Sunday, so weekends can be excluded when judging regularity
			"weekday": getdate(day).weekday(),
		},
	)
