from unittest.mock import patch

import frappe
from frappe.utils import add_days, today

from hrms.telemetry import capture_daily_attendance_pulse
from hrms.tests.utils import HRMSTestSuite


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


class TestTelemetry(HRMSTestSuite):
	def setUp(self):
		self.captured = []

		def collect(event, app, properties=None):
			self.captured.append((event, properties or {}))

		# Tests are a skipped context by design, and `_capture` would talk to the
		# real provider — stub both so the surrounding logic can be exercised.
		patches = [
			patch("hrms.telemetry._skip_context", return_value=False),
			patch("hrms.telemetry._capture", side_effect=collect),
			patch("hrms.telemetry.site_age", return_value=3),
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

	# ---- daily attendance pulse ----

	def test_daily_pulse_summarises_yesterday_not_today(self):
		"""The scheduler runs just after midnight, so `today` is always ~empty."""
		employee = create_employee(f"_Test Pulse {frappe.generate_hash(length=8)}")
		yesterday = add_days(today(), -1)

		create_checkin(employee.name, f"{yesterday} 09:30:00")
		create_checkin(employee.name, f"{yesterday} 18:30:00")
		create_checkin(employee.name, f"{today()} 09:30:00")

		with self.telemetry_enabled():
			capture_daily_attendance_pulse()

		summaries = self.events("attendance_daily_summary")
		self.assertEqual(len(summaries), 1)

		summary = summaries[0]
		expected = frappe.db.count(
			"Employee Checkin", {"time": ["between", [f"{yesterday} 00:00:00", f"{yesterday} 23:59:59"]]}
		)
		self.assertEqual(summary["checkins"], expected)
		self.assertGreaterEqual(summary["checkins"], 2)
		self.assertGreaterEqual(summary["employees_checked_in"], 1)
		self.assertGreater(summary["checkin_participation_rate"], 0)

	def test_daily_pulse_weekday_describes_the_summarised_day(self):
		create_employee(f"_Test Pulse {frappe.generate_hash(length=8)}")

		with self.telemetry_enabled():
			capture_daily_attendance_pulse()

		summary = self.events("attendance_daily_summary")[0]
		self.assertEqual(summary["weekday"], frappe.utils.getdate(add_days(today(), -1)).weekday())

	# ---- first-time milestones ----

	def test_milestone_fires_for_doctype_seeded_at_install(self):
		"""`leave_type_configured` never fired: install seeds several Leave Types,
		and the old row-count gate treated that as "not the first one"."""
		self.assertGreater(frappe.db.count("Leave Type"), 1, "expected seeded Leave Types")
		frappe.defaults.clear_default("hrms_milestone:leave_type_configured")

		frappe.get_doc(
			{"doctype": "Leave Type", "leave_type_name": f"_Test LT {frappe.generate_hash(length=8)}"}
		).insert()

		self.assertEqual(len(self.events("leave_type_configured")), 1)

	def test_milestone_fires_only_once_per_site(self):
		frappe.defaults.clear_default("hrms_milestone:leave_type_configured")

		for _ in range(3):
			frappe.get_doc(
				{"doctype": "Leave Type", "leave_type_name": f"_Test LT {frappe.generate_hash(length=8)}"}
			).insert()

		self.assertEqual(len(self.events("leave_type_configured")), 1)

	def test_milestone_carries_day_since_install(self):
		frappe.defaults.clear_default("hrms_milestone:leave_type_configured")

		frappe.get_doc(
			{"doctype": "Leave Type", "leave_type_name": f"_Test LT {frappe.generate_hash(length=8)}"}
		).insert()

		self.assertEqual(self.events("leave_type_configured")[0]["day_since_install"], 3)

	def test_milestone_skipped_outside_activation_window(self):
		frappe.defaults.clear_default("hrms_milestone:leave_type_configured")

		with patch("hrms.telemetry.site_age", return_value=90):
			frappe.get_doc(
				{"doctype": "Leave Type", "leave_type_name": f"_Test LT {frappe.generate_hash(length=8)}"}
			).insert()

		self.assertEqual(self.events("leave_type_configured"), [])
