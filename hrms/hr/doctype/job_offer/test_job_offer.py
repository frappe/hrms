# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, nowdate

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.job_applicant.job_applicant import get_applicant_to_hire_percentage
from hrms.hr.doctype.job_offer.job_offer import (
	compute_compensation,
	copy_regional_config,
	get_offer_acceptance_rate,
)
from hrms.hr.doctype.staffing_plan.test_staffing_plan import make_company
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	PERIODS_PER_YEAR,
)
from hrms.payroll.doctype.salary_structure_assignment.test_salary_structure_assignment import (
	_make_component,
)
from hrms.tests.test_utils import create_job_applicant
from hrms.tests.utils import HRMSTestSuite


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
		job_offer = create_job_offer()
		job_offer.save()
		job_offer.discard()
		job_offer.reload()
		self.assertEqual(job_offer.status, "Cancelled")

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

	def test_breakup_closes_with_ctc_and_take_home_rows(self):
		"""Take Home is CTC less the employer's own off-slip cost."""
		base = 50000
		structure = make_capped_pf_structure("Test Offer Summary Structure")
		details = compute_from_base(structure.name, base)

		summaries = summary_rows(details)
		self.assertEqual(list(summaries), ["Total Cost to Company (CTC)", "Take Home"])
		self.assertEqual([row["is_summary"] for row in details["components"][-2:]], [1, 1])

		employer_yearly = 1800 * 12
		self.assertAlmostEqual(summaries["Total Cost to Company (CTC)"]["yearly"], details["ctc"], places=2)
		self.assertAlmostEqual(summaries["Take Home"]["yearly"], details["ctc"] - employer_yearly, places=2)
		self.assertAlmostEqual(
			summaries["Total Cost to Company (CTC)"]["per_cycle"], details["ctc"] / 12, places=2
		)

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
		# with nothing for the employer to bear off-slip, Take Home is the whole CTC
		self.assertAlmostEqual(summary_rows(details)["Take Home"]["yearly"], details["ctc"], places=2)

	def test_returns_nothing_without_base(self):
		structure = make_salary_structure(
			"Test Offer CTC Empty Structure", "Monthly", base=50000, currency="INR"
		)
		details = compute_from_base(structure.name, 0)

		self.assertEqual(details["components"], [])
		self.assertEqual(details["ctc"], 0)

	def test_solves_base_across_an_employer_contribution_cap(self):
		"""The probes land below the PF wage cap and the answer above it, so the fitted
		line does not hold where the answer lies. A solver that trusted the fit would
		return 44642.86 (CTC 289457) instead of 46400."""
		structure = make_capped_pf_structure("Test Offer Cap Structure")

		details = compute_from_ctc(structure.name, 300000)

		self.assertAlmostEqual(details["base"], 46400, delta=0.05)
		self.assertAlmostEqual(details["ctc"], 300000, delta=1)
		self.assertFalse(details["ctc_adjusted"])

		# the answer the two probes' line points at, had it been trusted unverified
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
		"""A stepped formula makes CTC a staircase in multiples of 12000, so 300500 has
		no base that produces it."""
		structure = make_stepped_structure("Test Offer Stepped Structure")

		details = compute_from_ctc(structure.name, 300500)

		self.assertTrue(details["ctc_adjusted"])
		self.assertAlmostEqual(details["ctc"], 312000, delta=1)
		self.assertNotAlmostEqual(details["ctc"], 300500, delta=1)

	def test_base_independent_structure_does_not_divide_by_zero(self):
		"""Every component is a fixed amount, so CTC never moves with base and the fitted
		slope is zero."""
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
		"""A regional app opts an offer into statutory employer costs by adding the same
		fieldname to Job Offer, without hrms naming anything region-specific."""
		make_shared_custom_field("test_epf_applicable")
		self.addCleanup(remove_shared_custom_field, "test_epf_applicable")

		offer = make_offer_doc("Irrelevant For This Test", test_epf_applicable=1, ctc=999)
		assignment = frappe.new_doc("Salary Structure Assignment")

		copy_regional_config(offer, assignment)

		self.assertEqual(assignment.get("test_epf_applicable"), 1)
		# standard fields are set deliberately, never swept across by matching name --
		# ctc exists on both doctypes and must not leak from the offer
		self.assertFalse(assignment.ctc)

	def test_regional_config_ignores_fields_the_offer_does_not_have(self):
		"""A statutory field that exists only on the assignment must be left at its own
		default rather than blanked by the offer."""
		make_shared_custom_field("test_assignment_only_flag", on_job_offer=False)
		self.addCleanup(remove_shared_custom_field, "test_assignment_only_flag")

		assignment = frappe.new_doc("Salary Structure Assignment")
		assignment.test_assignment_only_flag = 1

		copy_regional_config(make_offer_doc("Irrelevant For This Test"), assignment)

		self.assertEqual(assignment.get("test_assignment_only_flag"), 1)

	def test_offer_without_a_salary_structure_asks_for_no_compensation(self):
		"""An offer that carries no salary structure must not demand a base or a basis. Built
		through new_doc, since that is what applies field defaults -- get_doc(dict) does not,
		which is how a stored default slipped past the other tests."""
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

		# and a basis on its own must not demand a base either -- only a structure does
		offer.calculate_component_amount_from = "Base and Variable"
		offer.save()

		self.assertFalse(offer.base)
		self.assertFalse(offer.ctc_breakup)

	def test_compensation_is_set_on_save_without_the_form(self):
		"""REST, data import and the Employee override all save a Job Offer without the
		client script ever running."""
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
			["Total Cost to Company (CTC)", "Take Home"],
		)


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
	"""An unsaved Job Offer carrying only what the compensation maths reads."""
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
	"""Basic is half of base; employer PF is 12% of Basic but only up to a wage of 15000,
	so CTC is 6.72 * base below the cap and 6 * base + 21600 above it."""
	_make_component("JO Test Basic", "JOTB", "Earning", amount_based_on_formula=1, formula="base * 0.5")
	_make_component(
		"JO Test Employer PF",
		"JOTEPF",
		"Employer Contribution",
		amount_based_on_formula=1,
		formula="min(JOTB, 15000) * 0.12",
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
	if not args.job_applicant:
		job_applicant = create_job_applicant()

	if not frappe.db.exists("Designation", args.designation):
		create_designation(designation_name=args.designation)

	job_offer = frappe.get_doc(
		{
			"doctype": "Job Offer",
			"job_applicant": args.job_applicant or job_applicant.name,
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
