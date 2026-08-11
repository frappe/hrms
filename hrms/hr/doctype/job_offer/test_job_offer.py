# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, nowdate

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.job_applicant.job_applicant import get_applicant_to_hire_percentage
from hrms.hr.doctype.job_offer.job_offer import get_ctc_breakup, get_offer_acceptance_rate
from hrms.hr.doctype.staffing_plan.test_staffing_plan import make_company
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	PERIODS_PER_YEAR,
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

	def test_ctc_breakup_agrees_with_salary_structure_assignment(self):
		base = 50000
		employee = make_employee("test_offer_ctc@example.com", company="_Test Company")
		structure = make_salary_structure(
			"Test Offer CTC Structure", "Monthly", employee=employee, base=base, currency="INR"
		)
		assignment = frappe.get_last_doc(
			"Salary Structure Assignment", filters={"employee": employee, "docstatus": 1}
		)

		breakup = get_ctc_breakup(
			salary_structure=structure.name, company="_Test Company", base=base, currency="INR"
		)

		self.assertTrue(breakup)
		self.assertAlmostEqual(breakup[-1]["yearly"], assignment.ctc, places=2)

	def test_ctc_breakup_rows_sum_to_ctc_row(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Sum Structure", "Monthly", base=base, currency="INR"
		)
		breakup = get_ctc_breakup(
			salary_structure=structure.name, company="_Test Company", base=base, currency="INR"
		)

		component_total = sum(row["yearly"] for row in breakup[:-1])
		self.assertAlmostEqual(component_total, breakup[-1]["yearly"], places=2)

	def test_ctc_breakup_excludes_deductions(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Deduction Structure", "Monthly", base=base, currency="INR"
		)
		deduction_components = {row.salary_component for row in structure.deductions}
		self.assertTrue(deduction_components)

		breakup = get_ctc_breakup(
			salary_structure=structure.name, company="_Test Company", base=base, currency="INR"
		)
		labels = {row["fixed_component"] for row in breakup}

		self.assertFalse(labels & deduction_components)

	def test_ctc_breakup_labels_carry_no_abbreviation(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Label Structure", "Monthly", base=base, currency="INR"
		)
		breakup = get_ctc_breakup(
			salary_structure=structure.name, company="_Test Company", base=base, currency="INR"
		)

		for row in breakup[:-1]:
			self.assertNotIn("(", row["fixed_component"])

	def test_ctc_breakup_yearly_uses_periods_per_year(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC Weekly Structure", "Weekly", base=base, currency="INR"
		)
		breakup = get_ctc_breakup(
			salary_structure=structure.name, company="_Test Company", base=base, currency="INR"
		)

		periods = PERIODS_PER_YEAR["Weekly"]
		for row in breakup:
			self.assertAlmostEqual(row["yearly"], row["per_cycle"] * periods, places=2)

	def test_ctc_breakup_without_employer_contributions(self):
		base = 50000
		structure = make_salary_structure(
			"Test Offer CTC No Employer Structure",
			"Monthly",
			base=base,
			currency="INR",
			deductions=[],
		)
		self.assertFalse(structure.employer_contributions)

		breakup = get_ctc_breakup(
			salary_structure=structure.name, company="_Test Company", base=base, currency="INR"
		)
		earnings_total = sum(row["yearly"] for row in breakup[:-1])

		self.assertAlmostEqual(breakup[-1]["yearly"], earnings_total, places=2)

	def test_ctc_breakup_returns_nothing_without_base(self):
		structure = make_salary_structure(
			"Test Offer CTC Empty Structure", "Monthly", base=50000, currency="INR"
		)
		self.assertEqual(
			get_ctc_breakup(salary_structure=structure.name, company="_Test Company", base=0), []
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
