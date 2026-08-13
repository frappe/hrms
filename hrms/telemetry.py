import frappe
from frappe.query_builder.functions import Count
from frappe.utils import add_days, date_diff, getdate, today
from frappe.utils.telemetry import capture as _capture
from frappe.utils.telemetry import site_age

APP = "hrms"
ACTIVATION_WINDOW_DAYS = 30


def _skip_context() -> bool:
	"""Don't record telemetry from automated / non-interactive runs."""
	return bool(
		frappe.flags.in_install
		or frappe.flags.in_migrate
		or frappe.flags.in_patch
		or frappe.flags.in_test
		or frappe.flags.in_import
	)


def capture(event: str, properties: dict | None = None) -> None:
	"""Record an HR usage event (fires on every occurrence)."""
	if _skip_context():
		return

	_capture(event, APP, properties=properties or {})


def _claim_milestone(event: str) -> bool:
	"""Claim a once-per-site milestone. Returns False if it already fired.

	This used to be inferred by counting existing rows of the doctype, which
	silently swallowed any milestone whose doctype ships install-time fixtures:
	`make_fixtures()` seeds five Leave Types at install, so the count was always
	>1 by the time a user created one and `leave_type_configured` never fired.
	A claim flag is also immune to bulk imports and to rows being deleted and
	recreated later.
	"""
	key = f"hrms_milestone:{event}"
	if frappe.db.get_default(key):
		return False

	frappe.db.set_default(key, "1")
	return True


def capture_first(event: str, properties: dict | None = None) -> None:
	if _skip_context():
		return

	age = site_age()
	if not age or age > ACTIVATION_WINDOW_DAYS:
		return

	if not _claim_milestone(event):
		return

	capture(event, {"day_since_install": age, **(properties or {})})


def _duration_days(from_date, to_date) -> int | None:
	if not (from_date and to_date):
		return None
	return date_diff(to_date, from_date) + 1


def on_leave_application_submit(doc, method=None):
	capture(
		"leave_application_submitted",
		{
			"leave_type": doc.leave_type,
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
			"total_claimed_amount": doc.total_claimed_amount,
			"expense_count": len(doc.expenses or []),
			"is_paid": bool(doc.is_paid),
			"has_advances": bool(doc.get("advances")),
			"has_taxes": bool(doc.get("taxes")),
		},
	)
	capture_first("first_expense_claimed")


# Standard `Attendance Request.reason` Select options. Anything outside this set
# (e.g. a site that customised the field into free-text) is coarsened to "other"
# so raw user-entered notes never leave the site.
ATTENDANCE_REQUEST_REASONS = {"Work From Home", "On Duty"}


def on_attendance_request_submit(doc, method=None):
	capture(
		"attendance_request_submitted",
		{
			"reason": doc.reason if doc.reason in ATTENDANCE_REQUEST_REASONS else "other",
			"half_day": bool(doc.half_day),
			"include_holidays": bool(doc.include_holidays),
			"days": _duration_days(doc.from_date, doc.to_date),
		},
	)


def on_shift_request_submit(doc, method=None):
	capture(
		"shift_request_submitted",
		{
			"shift_type": doc.shift_type,
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
			"final_score": doc.final_score,
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
	if _skip_context() or not frappe.get_system_settings("enable_telemetry"):
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

	capture(
		"attendance_daily_summary",
		{
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
