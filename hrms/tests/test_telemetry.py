from unittest.mock import patch

import frappe
from frappe.utils import add_days, getdate

from hrms.telemetry import (
	CONVERSION_EVENT,
	FIRST_CAPTURE_MILESTONE,
	MILESTONE_DOCTYPE,
	_claim_milestone,
	capture,
	capture_daily_attendance_pulse,
)
from hrms.tests.utils import HRMSTestSuite

# A fixed Wednesday. The daily pulse reads the clock and summarises the day
# before, so anything derived from the real clock makes these tests fail when a
# run straddles midnight. Freeze it instead of computing from `today()`.
FROZEN_TODAY = "2026-03-12"
FROZEN_YESTERDAY = "2026-03-11"


def create_employee(employee_name: str):
	return frappe.get_doc(
		{
			"doctype": "Employee",
			"employee_name": employee_name,
			"first_name": employee_name,
			"gender": "Male",
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2020-01-01",
			"company": "_Test Company",
			"status": "Active",
		}
	).insert()


def create_checkin(employee: str, time: str):
	return frappe.get_doc(
		{"doctype": "Employee Checkin", "employee": employee, "time": time, "log_type": "IN"}
	).insert()


def create_leave_type():
	return frappe.get_doc(
		{"doctype": "Leave Type", "leave_type_name": f"_Test LT {frappe.generate_hash(length=8)}"}
	).insert()


class TestTelemetry(HRMSTestSuite):
	def setUp(self):
		self.captured = []

		def collect(event, app, properties=None):
			self.captured.append((event, properties or {}))

		# Tests are a skipped context by design, and `_capture` would talk to the
		# real provider — stub both so the surrounding logic can be exercised.
		# `today` is stubbed in the module under test so the clock cannot advance
		# mid-test; `add_days`/`getdate` stay real and derive from the frozen value.
		patches = [
			patch("hrms.telemetry._skip_context", return_value=False),
			patch("hrms.telemetry._capture", side_effect=collect),
			patch("hrms.telemetry.site_age", return_value=3),
			patch("hrms.telemetry.today", return_value=FROZEN_TODAY),
		]
		for p in patches:
			p.start()
			self.addCleanup(p.stop)

	def events(self, name: str) -> list[dict]:
		return [props for event, props in self.captured if event == name]

	def telemetry_enabled(self):
		"""Force only `enable_telemetry` on; other settings (timezone) must pass through."""
		real = frappe.get_system_settings
		return patch(
			"frappe.get_system_settings",
			side_effect=lambda key: 1 if key == "enable_telemetry" else real(key),
		)

	def release_milestone(self, event: str):
		frappe.db.delete(MILESTONE_DOCTYPE, {"event": event})

	def start_conversion_clock(self, days_ago: int):
		"""Reset both conversion milestones and backdate `first_capture`."""
		self.release_milestone(CONVERSION_EVENT)
		self.release_milestone(FIRST_CAPTURE_MILESTONE)
		frappe.get_doc({"doctype": MILESTONE_DOCTYPE, "event": FIRST_CAPTURE_MILESTONE}).insert()
		frappe.db.set_value(
			MILESTONE_DOCTYPE,
			FIRST_CAPTURE_MILESTONE,
			"creation",
			f"{add_days(FROZEN_TODAY, -days_ago)} 10:00:00",
		)

	def reset_checkins(self):
		"""The pulse counts site-wide, so leftover rows on the frozen dates would
		let a wrong day coincidentally match the right one."""
		frappe.db.delete(
			"Employee Checkin",
			{"time": ["between", [f"{FROZEN_YESTERDAY} 00:00:00", f"{FROZEN_TODAY} 23:59:59"]]},
		)

	def checkins_on(self, day: str) -> int:
		return frappe.db.count(
			"Employee Checkin", {"time": ["between", [f"{day} 00:00:00", f"{day} 23:59:59"]]}
		)

	# ---- daily attendance pulse ----

	def test_daily_pulse_summarises_yesterday_not_today(self):
		"""The scheduler runs just after midnight, so `today` is always ~empty.

		The two days carry different counts on purpose — equal counts would let a
		summary of the wrong day pass.
		"""
		self.reset_checkins()
		employee = create_employee(f"_Test Pulse {frappe.generate_hash(length=8)}")

		create_checkin(employee.name, f"{FROZEN_YESTERDAY} 09:30:00")
		create_checkin(employee.name, f"{FROZEN_YESTERDAY} 13:00:00")
		create_checkin(employee.name, f"{FROZEN_YESTERDAY} 18:30:00")
		create_checkin(employee.name, f"{FROZEN_TODAY} 09:30:00")

		self.assertEqual(self.checkins_on(FROZEN_YESTERDAY), 3)
		self.assertEqual(self.checkins_on(FROZEN_TODAY), 1)

		with self.telemetry_enabled():
			capture_daily_attendance_pulse()

		summaries = self.events("attendance_daily_summary")
		self.assertEqual(len(summaries), 1)

		summary = summaries[0]
		self.assertEqual(summary["checkins"], 3)
		self.assertEqual(summary["employees_checked_in"], 1)
		self.assertGreater(summary["checkin_participation_rate"], 0)

	def test_daily_pulse_reports_zero_when_only_today_has_checkins(self):
		"""The exact shape of the bug: a day's worth of check-ins sitting in
		`today` must not be summarised, and must not be silently substituted."""
		self.reset_checkins()
		employee = create_employee(f"_Test Pulse {frappe.generate_hash(length=8)}")
		create_checkin(employee.name, f"{FROZEN_TODAY} 09:30:00")
		create_checkin(employee.name, f"{FROZEN_TODAY} 18:30:00")

		with self.telemetry_enabled():
			capture_daily_attendance_pulse()

		summary = self.events("attendance_daily_summary")[0]
		self.assertEqual(summary["checkins"], 0)
		self.assertEqual(summary["employees_checked_in"], 0)
		self.assertEqual(summary["checkin_participation_rate"], 0)

	def test_daily_pulse_weekday_describes_the_summarised_day(self):
		create_employee(f"_Test Pulse {frappe.generate_hash(length=8)}")

		with self.telemetry_enabled():
			capture_daily_attendance_pulse()

		summary = self.events("attendance_daily_summary")[0]
		# 2026-03-11 is a Wednesday; weekday() counts Monday as 0.
		self.assertEqual(summary["weekday"], 2)
		self.assertEqual(summary["weekday"], getdate(add_days(FROZEN_TODAY, -1)).weekday())

	# ---- first-time milestones ----

	def test_milestone_fires_for_doctype_seeded_at_install(self):
		"""`leave_type_configured` never fired: install seeds several Leave Types,
		and the old row-count gate treated that as "not the first one"."""
		self.assertGreater(frappe.db.count("Leave Type"), 1, "expected seeded Leave Types")
		self.release_milestone("leave_type_configured")

		create_leave_type()

		self.assertEqual(len(self.events("leave_type_configured")), 1)

	def test_milestone_fires_only_once_per_site(self):
		self.release_milestone("leave_type_configured")

		for _ in range(3):
			create_leave_type()

		self.assertEqual(len(self.events("leave_type_configured")), 1)

	def test_milestone_carries_day_since_install(self):
		self.release_milestone("leave_type_configured")

		create_leave_type()

		self.assertEqual(self.events("leave_type_configured")[0]["day_since_install"], 3)

	def test_milestone_skipped_outside_activation_window(self):
		self.release_milestone("leave_type_configured")

		with patch("hrms.telemetry.site_age", return_value=90):
			create_leave_type()

		self.assertEqual(self.events("leave_type_configured"), [])

	# ---- conversion ----

	def test_first_capture_starts_the_clock_without_firing_an_event(self):
		self.release_milestone(CONVERSION_EVENT)
		self.release_milestone(FIRST_CAPTURE_MILESTONE)

		capture("_test_usage")

		self.assertTrue(frappe.db.exists(MILESTONE_DOCTYPE, FIRST_CAPTURE_MILESTONE))
		self.assertEqual(self.events(CONVERSION_EVENT), [])
		self.assertEqual(self.events(FIRST_CAPTURE_MILESTONE), [])

	def test_no_conversion_within_fourteen_days_of_first_capture(self):
		self.start_conversion_clock(days_ago=14)

		capture("_test_usage")

		self.assertEqual(self.events(CONVERSION_EVENT), [])

	def test_usage_beyond_fourteen_days_converts_the_site(self):
		self.start_conversion_clock(days_ago=15)

		capture("_test_usage")

		conversions = self.events(CONVERSION_EVENT)
		self.assertEqual(len(conversions), 1)
		self.assertEqual(conversions[0]["days_since_first_capture"], 15)
		self.assertEqual(conversions[0]["day_since_install"], 3)

	def test_conversion_fires_only_once_per_site(self):
		self.start_conversion_clock(days_ago=30)

		for _ in range(3):
			capture("_test_usage")

		self.assertEqual(len(self.events(CONVERSION_EVENT)), 1)

	def test_daily_pulse_does_not_start_the_conversion_clock(self):
		"""The pulse is scheduler output, not usage: a site that set up employees
		and walked away would otherwise convert on cron activity alone."""
		# Created first: the Employee insert hook is itself usage and would
		# stamp `first_capture` before the pulse gets a chance to.
		create_employee(f"_Test Pulse {frappe.generate_hash(length=8)}")
		self.release_milestone(CONVERSION_EVENT)
		self.release_milestone(FIRST_CAPTURE_MILESTONE)

		with self.telemetry_enabled():
			capture_daily_attendance_pulse()

		self.assertEqual(len(self.events("attendance_daily_summary")), 1)
		self.assertFalse(frappe.db.exists(MILESTONE_DOCTYPE, FIRST_CAPTURE_MILESTONE))

	def test_daily_pulse_does_not_convert_the_site(self):
		create_employee(f"_Test Pulse {frappe.generate_hash(length=8)}")
		self.start_conversion_clock(days_ago=15)

		with self.telemetry_enabled():
			capture_daily_attendance_pulse()

		self.assertEqual(self.events(CONVERSION_EVENT), [])

	# ---- the claim is atomic ----

	def test_claim_is_exclusive(self):
		self.release_milestone("_test_claim")

		self.assertTrue(_claim_milestone("_test_claim"))
		self.assertFalse(_claim_milestone("_test_claim"))
		self.assertEqual(frappe.db.count(MILESTONE_DOCTYPE, {"event": "_test_claim"}), 1)

	def test_claim_loses_to_a_row_written_by_another_transaction(self):
		"""A concurrent claim that commits first leaves the row behind; the loser
		must detect that from the row alone, with no read-then-write window."""
		self.release_milestone("_test_claim")
		frappe.get_doc({"doctype": MILESTONE_DOCTYPE, "event": "_test_claim"}).insert()

		self.assertFalse(_claim_milestone("_test_claim"))

	def test_claim_does_not_depend_on_reading_a_flag_first(self):
		"""Guards against reintroducing the read-then-write race: even if a lookup
		insists the milestone is unclaimed, the second claim must still fail."""
		self.release_milestone("_test_claim")

		with patch.object(frappe.db, "get_default", return_value=None):
			results = [_claim_milestone("_test_claim") for _ in range(2)]

		self.assertEqual(results, [True, False])
		self.assertEqual(frappe.db.count(MILESTONE_DOCTYPE, {"event": "_test_claim"}), 1)

	def test_duplicate_claim_leaves_the_transaction_usable(self):
		"""The rejected insert must not poison the surrounding transaction — the
		document being observed still has to save."""
		self.release_milestone("_test_claim")
		_claim_milestone("_test_claim")

		self.assertFalse(_claim_milestone("_test_claim"))

		leave_type = create_leave_type()
		self.assertTrue(frappe.db.exists("Leave Type", leave_type.name))

	def test_claim_is_enforced_by_the_database(self):
		"""The exclusivity is a primary-key constraint, not application logic."""
		self.release_milestone("_test_claim")
		frappe.get_doc({"doctype": MILESTONE_DOCTYPE, "event": "_test_claim"}).insert()

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({"doctype": MILESTONE_DOCTYPE, "event": "_test_claim"}).insert()
