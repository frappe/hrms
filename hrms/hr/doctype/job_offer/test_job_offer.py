# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, get_weekday, getdate, nowdate

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.job_applicant.job_applicant import get_applicant_to_hire_percentage
from hrms.hr.doctype.job_offer.job_offer import (
	compute_compensation,
	copy_regional_config,
	get_holiday_summary,
	get_leave_allocations,
	get_offer_acceptance_rate,
)
from hrms.hr.doctype.job_offer.job_offer import make_employee as make_employee_from_job_offer
from hrms.hr.doctype.staffing_plan.test_staffing_plan import make_company
from hrms.overrides.employee_master import update_job_applicant_and_offer
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	PERIODS_PER_YEAR,
)
from hrms.payroll.doctype.salary_structure_assignment.test_salary_structure_assignment import (
	_make_component,
)
from hrms.tests.test_utils import create_job_applicant
from hrms.tests.utils import HRMSTestSuite

TAKE_HOME = "Take Home* (Income Tax applicable as per IT Act)"


class TestJobOffer(HRMSTestSuite):
	def setUp(self):
		create_designation(designation_name="Researcher")

	def test_job_offer_creation_against_vacancies(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 1)
		job_applicant = create_job_applicant(email_id="test_job_offer@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant.name, designation="UX Designer")

		create_staffing_plan(
			name="Test No Vacancies",
			staffing_details=[
				{"designation": "UX Designer", "vacancies": 0, "estimated_cost_per_position": 5000}
			],
			company="_Test Company",
		)
		self.assertRaises(frappe.ValidationError, job_offer.submit)

		# test creation of job offer when vacancies are not present
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		job_offer.submit()
		self.assertTrue(frappe.db.exists("Job Offer", job_offer.name))

	def test_job_applicant_update(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		create_staffing_plan()
		job_applicant = create_job_applicant(email_id="test_job_applicants@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant.name)
		job_offer.submit()
		job_applicant.reload()
		self.assertEqual(job_applicant.status, "Accepted")

		# status update after rejection
		job_offer.status = "Rejected"
		job_offer.submit()
		job_applicant.reload()
		self.assertEqual(job_applicant.status, "Rejected")
		frappe.db.set_single_value("HR Settings", "check_vacancies", 1)

	def test_recruitment_metrics(self):
		job_applicant1 = create_job_applicant(email_id="test_job_applicant1@example.com")
		job_applicant2 = create_job_applicant(email_id="test_job_applicant2@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant1.name)
		job_offer.status = "Accepted"
		job_offer.submit()

		self.assertEqual(get_applicant_to_hire_percentage().get("value"), 50)

		job_offer = create_job_offer(job_applicant=job_applicant2.name)
		job_offer.status = "Rejected"
		job_offer.submit()

		self.assertEqual(get_offer_acceptance_rate().get("value"), 50)

	def test_status_on_save(self):
		job_applicant = create_job_applicant(email_id="test_job_offer_status@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant.name)
		job_offer.save()
		job_offer.discard()
		job_offer.reload()
		self.assertEqual(job_offer.status, "Cancelled")

	def test_job_offer_without_job_applicant(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		job_offer = create_job_offer(
			applicant_name="Walk In Candidate",
			applicant_email="walk_in_candidate@example.com",
			status="Awaiting Response",
		)
		job_offer.submit()

		job_offer.reload()
		self.assertFalse(job_offer.job_applicant)
		self.assertEqual(job_offer.applicant_name, "Walk In Candidate")

	def test_duplicate_job_offer_for_same_email(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		create_job_offer(
			applicant_name="Duplicate Candidate",
			applicant_email="duplicate_candidate@example.com",
			status="Awaiting Response",
		).submit()

		duplicate = create_job_offer(
			applicant_name="Duplicate Candidate",
			applicant_email="duplicate_candidate@example.com",
			status="Awaiting Response",
		)
		self.assertRaises(frappe.ValidationError, duplicate.save)

		# a different email is not a duplicate
		create_job_offer(
			applicant_name="Another Candidate",
			applicant_email="another_candidate@example.com",
			status="Awaiting Response",
		).save()

	def test_duplicate_job_offer_allowed_after_rejection(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		rejected = create_job_offer(
			applicant_name="Reoffered Candidate",
			applicant_email="reoffered_candidate@example.com",
			status="Rejected",
		)
		rejected.submit()

		create_job_offer(
			applicant_name="Reoffered Candidate",
			applicant_email="reoffered_candidate@example.com",
			status="Awaiting Response",
		).save()

	def test_make_employee_without_job_applicant(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		job_offer = create_job_offer(
			applicant_name="Intern Candidate",
			applicant_email="intern_candidate@example.com",
			status="Awaiting Response",
		)
		job_offer.submit()

		employee = make_employee_from_job_offer(job_offer.name)
		self.assertEqual(employee.first_name, "Intern Candidate")
		self.assertEqual(employee.personal_email, "intern_candidate@example.com")
		self.assertEqual(employee.job_offer, job_offer.name)

		employee.date_of_birth = "1990-05-08"
		employee.date_of_joining = nowdate()
		employee.gender = "Female"
		employee.insert()

		job_offer.reload()
		self.assertEqual(job_offer.status, "Accepted")

		job_offer.run_method("onload")
		self.assertEqual(job_offer.get_onload("employee"), employee.name)

	def test_onload_employee_ignores_unrelated_offers(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		unrelated = create_job_offer(
			applicant_name="Unrelated Candidate",
			applicant_email="unrelated_candidate@example.com",
			status="Awaiting Response",
		)
		unrelated.save()
		unrelated.run_method("onload")
		self.assertFalse(unrelated.get_onload("employee"))

	def test_rejected_job_offer_not_accepted_on_employee_creation(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		job_offer = create_job_offer(
			applicant_name="Rejected Candidate",
			applicant_email="rejected_candidate@example.com",
			status="Rejected",
		)
		job_offer.submit()

		employee = make_employee_from_job_offer(job_offer.name)
		employee.date_of_birth = "1990-05-08"
		employee.date_of_joining = nowdate()
		employee.gender = "Female"
		employee.insert()

		job_offer.reload()
		self.assertEqual(job_offer.status, "Rejected")

	def test_rejected_job_offer_does_not_accept_job_applicant(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		job_applicant = create_job_applicant(email_id="rejected_sync@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant.name, status="Rejected")
		job_offer.submit()

		update_job_applicant_and_offer(frappe._dict({"job_applicant": job_applicant.name}))

		job_applicant.reload()
		job_offer.reload()
		self.assertEqual(job_offer.status, "Rejected")
		self.assertEqual(job_applicant.status, "Rejected")

	def test_reoffered_applicant_accepts_live_job_offer(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		job_applicant = create_job_applicant(email_id="reoffered_pick@example.com")

		rejected = create_job_offer(job_applicant=job_applicant.name, status="Rejected")
		rejected.submit()
		live = create_job_offer(job_applicant=job_applicant.name, status="Awaiting Response")
		live.save()

		update_job_applicant_and_offer(frappe._dict({"job_applicant": job_applicant.name}))

		live.reload()
		rejected.reload()
		self.assertEqual(live.status, "Accepted")
		self.assertEqual(rejected.status, "Rejected")

	def test_ctc_agrees_with_salary_structure_assignment(self):
		base = 50000
		employee = make_employee("test_offer_ctc@example.com", company="_Test Company")
		structure = make_salary_structure(
			"Test Offer CTC Structure", "Monthly", employee=employee, base=base, currency="INR"
		)
		assignment = frappe.get_last_doc(
			"Salary Structure Assignment", filters={"employee": employee, "docstatus": 1}
		)

		details = compute_from_base(structure.name, base)

		self.assertTrue(details["components"])
		self.assertAlmostEqual(details["ctc"], assignment.ctc, places=2)

	def test_breakup_rows_sum_to_ctc(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Sum Structure", "Monthly", base=base, currency="INR"
		)
		details = compute_from_base(structure.name, base)

		component_total = sum(row["yearly"] for row in component_rows(details))
		self.assertAlmostEqual(component_total, details["ctc"], places=2)

	def test_breakup_excludes_deductions(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Deduction Structure", "Monthly", base=base, currency="INR"
		)
		deduction_components = {row.salary_component for row in structure.deductions}
		self.assertTrue(deduction_components)

		details = compute_from_base(structure.name, base)
		components = {row["fixed_components"] for row in component_rows(details)}

		self.assertFalse(components & deduction_components)

	def test_breakup_labels_carry_no_abbreviation(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Label Structure", "Monthly", base=base, currency="INR"
		)
		details = compute_from_base(structure.name, base)
		self.assertTrue(component_rows(details))

		for row in component_rows(details):
			self.assertNotIn("(", row["fixed_components"])

	def test_breakup_reads_top_to_bottom(self):
		base = 50000
		structure = make_capped_pf_structure("Test Offer Summary Structure")
		details = compute_from_base(structure.name, base)

		labels = [row["fixed_components"] for row in details["components"]]
		self.assertEqual(
			labels,
			[
				"JO Test Basic",
				"Gross Pay",
				"JO Test Employer PF",
				"Total Cost to Company (CTC)",
				TAKE_HOME,
			],
		)
		self.assertEqual([row["is_summary"] for row in details["components"]], [0, 1, 0, 1, 1])

		summaries = summary_rows(details)
		self.assertAlmostEqual(summaries["Gross Pay"]["per_cycle"], base * 0.5, places=2)
		self.assertAlmostEqual(summaries["Total Cost to Company (CTC)"]["yearly"], details["ctc"], places=2)
		self.assertAlmostEqual(
			summaries["Total Cost to Company (CTC)"]["per_cycle"], details["ctc"] / 12, places=2
		)

	def test_zero_components_are_left_out(self):
		base = 50000
		_make_component("JO Test Basic", "JOTB", "Earning", amount_based_on_formula=1, formula="base * 0.5")
		_make_component("JO Test Nil", "JOTN", "Earning", amount_based_on_formula=1, formula="0")
		structure = make_salary_structure(
			"Test Offer Nil Structure",
			"Monthly",
			currency="INR",
			earnings=[
				{
					"salary_component": "JO Test Basic",
					"abbr": "JOTB",
					"amount_based_on_formula": 1,
					"formula": "base * 0.5",
				},
				{
					"salary_component": "JO Test Nil",
					"abbr": "JOTN",
					"amount_based_on_formula": 1,
					"formula": "0",
				},
			],
			deductions=[],
		)
		details = compute_from_base(structure.name, base)

		labels = [row["fixed_components"] for row in details["components"]]
		self.assertIn("JO Test Basic", labels)
		self.assertNotIn("JO Test Nil", labels)

	def test_take_home_nets_off_employee_deductions(self):
		base = 50000
		_make_component("JO Test Basic", "JOTB", "Earning", amount_based_on_formula=1, formula="base * 0.5")
		_make_component("JO Test PT", "JOTPT", "Deduction", amount=200, depends_on_payment_days=0)
		structure = make_salary_structure(
			"Test Offer Take Home Structure",
			"Monthly",
			currency="INR",
			earnings=[
				{
					"salary_component": "JO Test Basic",
					"abbr": "JOTB",
					"amount_based_on_formula": 1,
					"formula": "base * 0.5",
				}
			],
			deductions=[{"salary_component": "JO Test PT", "abbr": "JOTPT", "amount": 200}],
		)
		details = compute_from_base(structure.name, base)

		summaries = summary_rows(details)
		gross = summaries["Gross Pay"]["per_cycle"]
		self.assertAlmostEqual(gross, base * 0.5, places=2)
		self.assertAlmostEqual(summaries[TAKE_HOME]["per_cycle"], gross - 200, places=2)

		self.assertNotIn("JO Test PT", [row["fixed_components"] for row in details["components"]])

	def test_gross_excludes_employer_contributions(self):
		base = 50000
		structure = make_capped_pf_structure("Test Offer Gross Structure")
		details = compute_from_base(structure.name, base)

		self.assertAlmostEqual(details["gross"], base * 0.5, places=2)

		employer_yearly = 1800 * 12
		self.assertAlmostEqual(details["ctc"] - details["gross"] * 12, employer_yearly, places=2)

	def test_gross_is_set_on_save_without_the_form(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		base = 50000
		structure = make_capped_pf_structure("Test Offer Gross Save Structure")
		applicant = create_job_applicant(email_id="test_offer_gross@example.com")

		offer = create_job_offer(
			job_applicant=applicant.name,
			salary_structure=structure.name,
			calculate_component_amount_from="Base and Variable",
			base=base,
			currency="INR",
		)
		offer.insert()

		self.assertAlmostEqual(offer.gross, base * 0.5, places=2)

	def test_gross_is_cleared_with_the_rest_of_the_compensation(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer Gross Clear Structure", "Monthly", base=base, currency="INR"
		)
		offer = make_offer_doc(structure.name, calculate_component_amount_from="Base and Variable", base=base)
		offer.set_compensation()
		self.assertGreater(offer.gross, 0)

		offer.salary_structure = None
		offer.set_compensation()
		self.assertFalse(offer.gross)

	def test_hand_edited_break_up_survives_a_re_save(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		base = 50000
		structure = make_capped_pf_structure("Test Offer Manual Rows Structure")
		applicant = create_job_applicant(email_id="test_offer_manual@example.com")

		offer = create_job_offer(
			job_applicant=applicant.name,
			salary_structure=structure.name,
			calculate_component_amount_from="Base and Variable",
			base=base,
			currency="INR",
		)
		offer.insert()
		self.assertIn("JO Test Basic", [row.fixed_components for row in offer.ctc_breakup])

		offer.append(
			"ctc_breakup",
			{"fixed_components": "Joining Bonus", "per_cycle": 5000, "yearly": 60000, "currency": "INR"},
		)
		offer.ctc_breakup = [row for row in offer.ctc_breakup if row.fixed_components != "JO Test Basic"]
		offer.save()

		labels = [row.fixed_components for row in offer.ctc_breakup]
		self.assertIn("Joining Bonus", labels)
		self.assertNotIn("JO Test Basic", labels)

	def test_renegotiating_the_pay_rebuilds_the_break_up(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		structure = make_capped_pf_structure("Test Offer Renegotiate Structure")
		applicant = create_job_applicant(email_id="test_offer_renegotiate@example.com")

		offer = create_job_offer(
			job_applicant=applicant.name,
			salary_structure=structure.name,
			calculate_component_amount_from="Base and Variable",
			base=50000,
			currency="INR",
		)
		offer.insert()

		offer.append(
			"ctc_breakup",
			{"fixed_components": "Joining Bonus", "per_cycle": 5000, "yearly": 60000, "currency": "INR"},
		)
		offer.base = 60000
		offer.save()

		labels = [row.fixed_components for row in offer.ctc_breakup]
		self.assertNotIn("Joining Bonus", labels)
		self.assertIn("JO Test Basic", labels)
		self.assertAlmostEqual(offer.gross, 30000, places=2)

	def test_yearly_uses_periods_per_year(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Weekly Structure", "Weekly", base=base, currency="INR"
		)
		details = compute_from_base(structure.name, base)

		periods = PERIODS_PER_YEAR["Weekly"]
		for row in details["components"]:
			self.assertAlmostEqual(row["yearly"], row["per_cycle"] * periods, places=2)

	def test_breakup_without_employer_contributions(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC No Employer Structure",
			"Monthly",
			base=base,
			currency="INR",
			deductions=[],
		)
		self.assertFalse(structure.employer_contributions)

		details = compute_from_base(structure.name, base)
		earnings_total = sum(row["yearly"] for row in component_rows(details))

		self.assertAlmostEqual(details["ctc"], earnings_total, places=2)
		self.assertAlmostEqual(summary_rows(details)[TAKE_HOME]["yearly"], details["ctc"], places=2)

	def test_returns_nothing_without_base(self):
		structure = make_salary_structure(
			"Test Offer CTC Empty Structure", "Monthly", base=50000, currency="INR"
		)
		details = compute_from_base(structure.name, 0)

		self.assertEqual(details["components"], [])
		self.assertEqual(details["ctc"], 0)

	def test_solves_base_across_an_employer_contribution_cap(self):
		structure = make_capped_pf_structure("Test Offer Cap Structure")

		details = compute_from_ctc(structure.name, 300000)

		self.assertAlmostEqual(details["base"], 46400, delta=0.05)
		self.assertAlmostEqual(details["ctc"], 300000, delta=1)
		self.assertFalse(details["ctc_adjusted"])

		self.assertAlmostEqual(compute_from_base(structure.name, 44642.86)["ctc"], 289457.16, delta=1)

	def test_mode_switch_is_lossless(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer Mode Switch Structure", "Monthly", base=base, currency="INR"
		)

		from_base = compute_from_base(structure.name, base)
		from_ctc = compute_from_ctc(structure.name, from_base["ctc"], base=base)

		self.assertAlmostEqual(from_ctc["base"], base, places=2)
		self.assertAlmostEqual(from_ctc["ctc"], from_base["ctc"], places=2)
		self.assertFalse(from_ctc["ctc_adjusted"])

	def test_unreachable_ctc_snaps_to_the_achievable_figure(self):
		structure = make_stepped_structure("Test Offer Stepped Structure")

		details = compute_from_ctc(structure.name, 300500)

		self.assertTrue(details["ctc_adjusted"])
		self.assertAlmostEqual(details["ctc"], 312000, delta=1)
		self.assertNotAlmostEqual(details["ctc"], 300500, delta=1)

	def test_base_independent_structure_does_not_divide_by_zero(self):
		_make_component("JO Test Flat", "JOTF", "Earning")
		structure = make_salary_structure(
			"Test Offer Flat Structure",
			"Monthly",
			currency="INR",
			earnings=[{"salary_component": "JO Test Flat", "abbr": "JOTF", "amount": 10000}],
			deductions=[],
		)

		details = compute_from_ctc(structure.name, 500000)

		self.assertTrue(details["ctc_adjusted"])
		self.assertAlmostEqual(details["ctc"], 120000, delta=1)

	def test_regional_config_is_carried_onto_the_prospective_assignment(self):
		make_shared_custom_field("test_epf_applicable")
		self.addCleanup(remove_shared_custom_field, "test_epf_applicable")

		offer = make_offer_doc("Irrelevant For This Test", test_epf_applicable=1, ctc=999)
		assignment = frappe.new_doc("Salary Structure Assignment")

		copy_regional_config(offer, assignment)

		self.assertEqual(assignment.get("test_epf_applicable"), 1)
		self.assertFalse(assignment.ctc)

	def test_regional_config_ignores_fields_the_offer_does_not_have(self):
		make_shared_custom_field("test_assignment_only_flag", on_job_offer=False)
		self.addCleanup(remove_shared_custom_field, "test_assignment_only_flag")

		assignment = frappe.new_doc("Salary Structure Assignment")
		assignment.test_assignment_only_flag = 1

		copy_regional_config(make_offer_doc("Irrelevant For This Test"), assignment)

		self.assertEqual(assignment.get("test_assignment_only_flag"), 1)

	def test_offer_without_a_salary_structure_asks_for_no_compensation(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		applicant = create_job_applicant(email_id="test_offer_no_structure@example.com")

		offer = frappe.new_doc("Job Offer")
		offer.update(
			{
				"job_applicant": applicant.name,
				"offer_date": nowdate(),
				"designation": "Researcher",
				"company": "_Test Company",
			}
		)

		self.assertFalse(offer.calculate_component_amount_from)
		self.assertFalse(offer.base)

		offer.insert()

		self.assertFalse(offer.ctc)
		self.assertFalse(offer.ctc_breakup)

		offer.calculate_component_amount_from = "Base and Variable"
		offer.save()

		self.assertFalse(offer.base)
		self.assertFalse(offer.ctc_breakup)

	def test_compensation_is_set_on_save_without_the_form(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		base = 50000
		structure = make_salary_structure("Test Offer Save Structure", "Monthly", base=base, currency="INR")
		applicant = create_job_applicant(email_id="test_offer_save@example.com")

		offer = create_job_offer(
			job_applicant=applicant.name,
			salary_structure=structure.name,
			calculate_component_amount_from="Base and Variable",
			base=base,
			currency="INR",
		)
		offer.insert()

		self.assertTrue(offer.ctc_breakup)
		self.assertGreater(offer.ctc, 0)
		components = [row for row in offer.ctc_breakup if not row.is_summary]
		self.assertAlmostEqual(sum(row.yearly for row in components), offer.ctc, places=2)
		self.assertEqual(
			[row.fixed_components for row in offer.ctc_breakup if row.is_summary],
			["Gross Pay", "Total Cost to Company (CTC)", TAKE_HOME],
		)

	def test_leave_allocations_follow_the_leave_policy(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		policy = make_leave_policy("Test Offer Leave Policy", [("_Test Leave Type", 15)])
		applicant = create_job_applicant(email_id="test_offer_leave@example.com")

		offer = create_job_offer(job_applicant=applicant.name, leave_policy=policy.name)
		offer.insert()

		self.assertEqual(
			[(row.leave_type, row.annual_allocation) for row in offer.leave_allocations],
			[("_Test Leave Type", 15)],
		)

		offer.leave_policy = None
		offer.save()
		self.assertFalse(offer.leave_allocations)

	def test_weekly_off_reads_the_days_not_the_holiday_list_field(self):
		holiday_list = make_holiday_list("Test Offer Weekend List", weekly_offs=["Saturday", "Sunday"])
		frappe.db.set_value("Holiday List", holiday_list, "weekly_off", "")

		summary = get_holiday_summary(holiday_list)

		self.assertEqual(summary["weekly_off_days"], "Saturday, Sunday")

	def test_public_holidays_exclude_weekly_offs(self):
		holiday_list = make_holiday_list("Test Offer Public List", weekly_offs=["Sunday"], public_holidays=3)

		summary = get_holiday_summary(holiday_list)

		self.assertEqual(summary["total_public_holidays"], 3)
		self.assertEqual(summary["weekly_off_days"], "Sunday")

	def test_holiday_summary_is_set_on_save_without_the_form(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		holiday_list = make_holiday_list("Test Offer Saved List", weekly_offs=["Sunday"], public_holidays=2)
		applicant = create_job_applicant(email_id="test_offer_holidays@example.com")

		offer = create_job_offer(job_applicant=applicant.name, holiday_list=holiday_list)
		offer.insert()

		self.assertEqual(offer.weekly_off_days, "Sunday")
		self.assertEqual(offer.total_public_holidays, 2)

	def test_offer_without_a_holiday_list_or_policy_says_nothing(self):
		self.assertEqual(get_leave_allocations(None), [])
		self.assertEqual(get_holiday_summary(None), {"weekly_off_days": "", "total_public_holidays": 0})


def component_rows(details):
	return [row for row in details["components"] if not row["is_summary"]]


def summary_rows(details):
	return {row["fixed_components"]: row for row in details["components"] if row["is_summary"]}


def make_shared_custom_field(fieldname, on_job_offer=True):
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	definition = {"fieldname": fieldname, "fieldtype": "Check", "label": "Test Statutory Flag"}
	fields = {"Salary Structure Assignment": [{**definition, "insert_after": "base"}]}
	if on_job_offer:
		fields["Job Offer"] = [{**definition, "insert_after": "ctc"}]

	create_custom_fields(fields)
	for doctype in fields:
		frappe.clear_cache(doctype=doctype)


def remove_shared_custom_field(fieldname):
	for doctype in ("Job Offer", "Salary Structure Assignment"):
		frappe.delete_doc_if_exists("Custom Field", f"{doctype}-{fieldname}")
		frappe.clear_cache(doctype=doctype)


def make_offer_doc(salary_structure, **values):
	return frappe.get_doc(
		{
			"doctype": "Job Offer",
			"company": "_Test Company",
			"salary_structure": salary_structure,
			"currency": "INR",
			**values,
		}
	)


def compute_from_base(salary_structure, base):
	return compute_compensation(
		make_offer_doc(salary_structure, calculate_component_amount_from="Base and Variable", base=base)
	)


def compute_from_ctc(salary_structure, ctc, base=None):
	return compute_compensation(
		make_offer_doc(salary_structure, calculate_component_amount_from="CTC", base=base, ctc=ctc)
	)


def make_capped_pf_structure(name):
	_make_component("JO Test Basic", "JOTB", "Earning", amount_based_on_formula=1, formula="base * 0.5")
	_make_component(
		"JO Test Employer PF",
		"JOTEPF",
		"Employer Contribution",
		amount_based_on_formula=1,
		formula="min(JOTB, 15000) * 0.12",
		depends_on_payment_days=0,
	)

	return make_salary_structure(
		name,
		"Monthly",
		currency="INR",
		earnings=[
			{
				"salary_component": "JO Test Basic",
				"abbr": "JOTB",
				"amount_based_on_formula": 1,
				"formula": "base * 0.5",
			}
		],
		deductions=[],
		other_details={
			"employer_contributions": [
				{
					"salary_component": "JO Test Employer PF",
					"abbr": "JOTEPF",
					"amount_based_on_formula": 1,
					"formula": "min(JOTB, 15000) * 0.12",
					"depends_on_payment_days": 0,
				}
			]
		},
	)


def make_stepped_structure(name):
	formula = "round(base / 1000) * 1000"
	_make_component("JO Test Stepped", "JOTS", "Earning", amount_based_on_formula=1, formula=formula)

	return make_salary_structure(
		name,
		"Monthly",
		currency="INR",
		earnings=[
			{
				"salary_component": "JO Test Stepped",
				"abbr": "JOTS",
				"amount_based_on_formula": 1,
				"formula": formula,
			}
		],
		deductions=[],
	)


def create_job_offer(**args):
	args = frappe._dict(args)
	if not args.job_applicant and not args.applicant_email:
		args.job_applicant = create_job_applicant().name

	if not frappe.db.exists("Designation", args.designation):
		create_designation(designation_name=args.designation)

	job_offer = frappe.get_doc(
		{
			"doctype": "Job Offer",
			"job_applicant": args.job_applicant,
			"offer_date": args.offer_date or nowdate(),
			"designation": args.designation or "Researcher",
			"status": args.status or "Accepted",
			"company": args.company or "_Test Company",
		}
	)
	job_offer.update(args)
	return job_offer


def create_staffing_plan(**args):
	args = frappe._dict(args)
	make_company()
	frappe.db.set_value("Company", "_Test Company", "is_group", 1)
	if frappe.db.exists("Staffing Plan", args.name or "Test"):
		return
	staffing_plan = frappe.get_doc(
		{
			"doctype": "Staffing Plan",
			"name": args.name or "Test",
			"from_date": args.from_date or nowdate(),
			"to_date": args.to_date or add_days(nowdate(), 10),
			"staffing_details": args.staffing_details
			or [{"designation": "Researcher", "vacancies": 1, "estimated_cost_per_position": 50000}],
			"company": args.company or "_Test Company",
		}
	)
	staffing_plan.insert()
	staffing_plan.submit()
	return staffing_plan


def make_leave_policy(title, allocations):
	if frappe.db.exists("Leave Policy", title):
		frappe.delete_doc("Leave Policy", title, force=True)

	for leave_type, _allocation in allocations:
		if not frappe.db.exists("Leave Type", leave_type):
			frappe.get_doc({"doctype": "Leave Type", "leave_type_name": leave_type}).insert()

	return frappe.get_doc(
		{
			"doctype": "Leave Policy",
			"title": title,
			"leave_policy_details": [
				{"leave_type": leave_type, "annual_allocation": allocation}
				for leave_type, allocation in allocations
			],
		}
	).insert()


def make_holiday_list(name, weekly_offs=None, public_holidays=0):
	if frappe.db.exists("Holiday List", name):
		frappe.delete_doc("Holiday List", name, force=True)

	from_date = getdate("2026-01-01")
	to_date = getdate("2026-12-31")

	holidays = []
	for day_name in weekly_offs or []:
		holidays += [
			{"holiday_date": day, "description": day_name, "weekly_off": 1}
			for day in weekdays_between(day_name, from_date, to_date)
		]

	holidays += [
		{"holiday_date": add_days(from_date, 14 * (index + 1)), "description": f"Holiday {index}"}
		for index in range(public_holidays)
	]

	return (
		frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": name,
				"from_date": from_date,
				"to_date": to_date,
				"holidays": holidays,
			}
		)
		.insert()
		.name
	)


def weekdays_between(day_name, from_date, to_date):
	day = getdate(from_date)
	days = []
	while day <= getdate(to_date):
		if get_weekday(day) == day_name:
			days.append(day)
		day = add_days(day, 1)
	return days
