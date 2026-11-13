# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, add_months, get_first_day, getdate

from hrms.hr.doctype.employee_promotion.employee_promotion import calculate_revised_ctc, get_salary_on
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	create_salary_structure_assignment,
	make_employee,
	make_salary_structure,
)
from hrms.payroll.doctype.salary_structure_assignment.test_salary_structure_assignment import (
	_make_component,
)
from hrms.tests.utils import HRMSTestSuite


class TestEmployeePromotion(HRMSTestSuite):
	def test_submit_before_promotion_date(self):
		employee = make_employee("employee@promotions.com", company="_Test Company")
		promotion = frappe.get_doc(
			{
				"doctype": "Employee Promotion",
				"employee": employee,
				"promotion_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					}
				],
			}
		)
		promotion.promotion_date = add_days(getdate(), 1)
		self.assertRaises(frappe.DocstatusTransitionError, promotion.submit)

		promotion.promotion_date = getdate()
		promotion.submit()
		self.assertEqual(promotion.docstatus, 1)

	def test_employee_history(self):
		for grade in ["L1", "L2"]:
			frappe.get_doc({"doctype": "Employee Grade", "__newname": grade}).insert()

		employee = make_employee(
			"test_employee_promotion@example.com",
			company="_Test Company",
			date_of_birth=getdate("30-09-1980"),
			date_of_joining=getdate("01-10-2021"),
			designation="Software Developer",
			grade="L1",
			salary_currency="INR",
			ctc="500000",
		)

		promotion = frappe.get_doc(
			{
				"doctype": "Employee Promotion",
				"employee": employee,
				"promotion_date": getdate(),
				"revised_ctc": "1000000",
				"promotion_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					},
					{"property": "Grade", "current": "L1", "new": "L2", "fieldname": "grade"},
				],
			}
		).submit()

		# employee fields updated
		employee = frappe.get_doc("Employee", employee)
		self.assertEqual(employee.grade, "L2")
		self.assertEqual(employee.designation, "Project Manager")
		self.assertEqual(employee.ctc, 1000000)

		# internal work history updated
		self.assertEqual(employee.internal_work_history[0].designation, "Software Developer")
		self.assertEqual(employee.internal_work_history[0].from_date, getdate("01-10-2021"))

		self.assertEqual(employee.internal_work_history[1].designation, "Project Manager")
		self.assertEqual(employee.internal_work_history[1].from_date, getdate())

		promotion.cancel()
		employee.reload()

		# fields restored
		self.assertEqual(employee.grade, "L1")
		self.assertEqual(employee.designation, "Software Developer")
		self.assertEqual(employee.ctc, 500000)

		# internal work history updated on cancellation
		self.assertEqual(len(employee.internal_work_history), 1)
		self.assertEqual(employee.internal_work_history[0].designation, "Software Developer")
		self.assertEqual(employee.internal_work_history[0].from_date, getdate("01-10-2021"))

	def test_current_salary_comes_from_assignment(self):
		employee, assignment = setup_employee_with_assignment("promotion_current@example.com")
		frappe.db.set_value("Employee", employee, "ctc", 500000)

		promotion = make_promotion(employee)

		self.assertEqual(promotion.current_salary_structure_assignment, assignment.name)
		self.assertEqual(promotion.salary_structure, assignment.salary_structure)
		self.assertEqual(promotion.current_base, 50000)
		self.assertEqual(promotion.current_ctc, 1032000)

	def test_revised_ctc_is_calculated_from_revised_base(self):
		employee, _assignment = setup_employee_with_assignment("promotion_revised@example.com")

		promotion = make_promotion(employee, revised_base=60000, revised_ctc=1)

		self.assertEqual(promotion.revised_ctc, 1226400)
		self.assertEqual(calculate_revised_ctc(promotion.as_dict()), 1226400)

	def test_revised_ctc_uses_promoted_grade(self):
		for grade in ["EP Test G1", "EP Test G2"]:
			if not frappe.db.exists("Employee Grade", grade):
				frappe.get_doc({"doctype": "Employee Grade", "__newname": grade}).insert()

		employee, _assignment = setup_employee_with_assignment("promotion_grade@example.com")
		frappe.db.set_value("Employee", employee, "grade", "EP Test G1")
		structure = make_promotion_structure(
			"EP Test Grade Structure",
			extra_earnings=[
				{
					"salary_component": "EP Test Bonus",
					"abbr": "EPTX",
					"condition": 'grade == "EP Test G2"',
					"amount": 10000,
				}
			],
		)

		promotion = make_promotion(
			employee,
			salary_structure=structure.name,
			revised_base=60000,
			promotion_details=[
				{"property": "Grade", "fieldname": "grade", "current": "EP Test G1", "new": "EP Test G2"}
			],
		)

		self.assertEqual(promotion.revised_ctc, 1346400)
		self.assertEqual(frappe.db.get_value("Employee", employee, "grade"), "EP Test G1")

	def test_submit_does_not_create_assignment(self):
		employee, _assignment = setup_employee_with_assignment("promotion_no_auto@example.com")

		promotion = make_promotion(employee, revised_base=60000)
		promotion.submit()

		self.assertFalse(promotion.new_salary_structure_assignment)
		self.assertEqual(frappe.db.count("Salary Structure Assignment", {"employee": employee}), 1)

	def test_created_assignment_is_a_draft_and_cancel_cancels_it(self):
		employee, old_assignment = setup_employee_with_assignment("promotion_submit@example.com")
		frappe.db.set_value("Employee", employee, "ctc", 500000)

		promotion = make_promotion(employee, revised_base=60000)
		self.assertRaises(frappe.ValidationError, promotion.make_salary_structure_assignment)
		promotion.submit()

		new_assignment = frappe.get_doc(
			"Salary Structure Assignment", promotion.make_salary_structure_assignment()
		)
		self.assertEqual(promotion.new_salary_structure_assignment, new_assignment.name)
		self.assertEqual(new_assignment.docstatus, 0)
		new_assignment.submit()

		self.assertEqual(new_assignment.from_date, getdate(promotion.promotion_date))
		self.assertEqual(new_assignment.base, 60000)
		self.assertEqual(new_assignment.ctc, 1226400)
		self.assertEqual(new_assignment.payroll_payable_account, old_assignment.payroll_payable_account)
		self.assertEqual(new_assignment.income_tax_slab, old_assignment.income_tax_slab)
		self.assertEqual(new_assignment.variable, old_assignment.variable)
		self.assertEqual(get_salary_on(employee, promotion.promotion_date).name, new_assignment.name)
		self.assertEqual(frappe.db.get_value("Employee", employee, "ctc"), 1226400)

		promotion.cancel()

		self.assertEqual(
			frappe.db.get_value("Salary Structure Assignment", new_assignment.name, "docstatus"), 2
		)
		self.assertEqual(get_salary_on(employee, promotion.promotion_date).name, old_assignment.name)
		self.assertEqual(frappe.db.get_value("Employee", employee, "ctc"), 1032000)

	def test_promotion_assignment_cannot_be_cancelled_on_its_own(self):
		employee, _assignment = setup_employee_with_assignment("promotion_link@example.com")
		promotion = make_promotion(employee, revised_base=60000)
		promotion.submit()

		new_assignment = frappe.get_doc(
			"Salary Structure Assignment", promotion.make_salary_structure_assignment()
		)
		new_assignment.submit()

		self.assertRaises(frappe.LinkExistsError, new_assignment.cancel)

	def test_assignment_is_created_once(self):
		employee, _assignment = setup_employee_with_assignment("promotion_once@example.com")
		promotion = make_promotion(employee, revised_base=60000)
		promotion.submit()
		stale_copy = frappe.get_doc("Employee Promotion", promotion.name)
		promotion.make_salary_structure_assignment()

		self.assertRaisesRegex(
			frappe.ValidationError, "already created", promotion.make_salary_structure_assignment
		)
		self.assertRaisesRegex(
			frappe.ValidationError, "already created", stale_copy.make_salary_structure_assignment
		)

	def test_cancel_deletes_draft_assignment(self):
		employee, _assignment = setup_employee_with_assignment("promotion_draft@example.com")
		promotion = make_promotion(employee, revised_base=60000)
		promotion.submit()
		draft = promotion.make_salary_structure_assignment()

		promotion.cancel()

		self.assertFalse(frappe.db.exists("Salary Structure Assignment", draft))
		self.assertFalse(promotion.new_salary_structure_assignment)

	def test_no_assignment_without_revised_base(self):
		employee, _assignment = setup_employee_with_assignment("promotion_no_base@example.com")

		promotion = make_promotion(employee, revised_ctc=1500000)
		self.assertEqual(promotion.revised_ctc, 1500000)
		promotion.submit()

		self.assertRaisesRegex(
			frappe.ValidationError, "Revised Base first", promotion.make_salary_structure_assignment
		)
		self.assertEqual(frappe.db.get_value("Employee", employee, "ctc"), 1500000)

	def test_assignment_on_promotion_date_blocks_creation(self):
		employee, assignment = setup_employee_with_assignment("promotion_same_date@example.com")

		promotion = make_promotion(employee, promotion_date=assignment.from_date, revised_base=60000)
		promotion.submit()

		self.assertRaisesRegex(
			frappe.ValidationError, "change the Promotion Date", promotion.make_salary_structure_assignment
		)

	def test_later_assignment_blocks_creation(self):
		employee, assignment = setup_employee_with_assignment("promotion_later@example.com")
		create_salary_structure_assignment(
			employee,
			assignment.salary_structure,
			from_date=get_first_day(add_months(getdate(), 1)),
			company="_Test Company",
			base=55000,
			allow_duplicate=True,
		)

		promotion = make_promotion(employee, revised_base=60000)
		promotion.submit()

		self.assertRaisesRegex(
			frappe.ValidationError, "change the Promotion Date", promotion.make_salary_structure_assignment
		)


def setup_employee_with_assignment(user):
	employee = make_employee(user, company="_Test Company")
	structure = make_promotion_structure("EP Test Structure")
	assignment = create_salary_structure_assignment(
		employee,
		structure.name,
		from_date=get_first_day(add_months(getdate(), -2)),
		company="_Test Company",
		base=50000,
	)
	return employee, assignment


def make_promotion_structure(name, extra_earnings=None):
	components = [
		("EP Test Basic", "EPTB", "Earning"),
		("EP Test HRA", "EPTH", "Earning"),
		("EP Test Special", "EPTS", "Earning"),
		("EP Test Bonus", "EPTX", "Earning"),
		("EP Test Employer PF", "EPTE", "Employer Contribution"),
	]
	for component, abbr, component_type in components:
		if not frappe.db.exists("Salary Component", component):
			_make_component(component, abbr, component_type, depends_on_payment_days=0)

	def row(component, abbr, formula=None, amount=0):
		return {
			"salary_component": component,
			"abbr": abbr,
			"amount_based_on_formula": 1 if formula else 0,
			"formula": formula,
			"amount": amount,
			"depends_on_payment_days": 0,
		}

	return make_salary_structure(
		name,
		"Monthly",
		currency="INR",
		earnings=[
			row("EP Test Basic", "EPTB", "base"),
			row("EP Test HRA", "EPTH", "base * 0.5"),
			row("EP Test Special", "EPTS", amount=5000),
			*(extra_earnings or []),
		],
		deductions=[],
		other_details={"employer_contributions": [row("EP Test Employer PF", "EPTE", "EPTB * 0.12")]},
	)


def make_promotion(employee, **values):
	promotion = frappe.get_doc(
		{
			"doctype": "Employee Promotion",
			"employee": employee,
			"promotion_date": getdate(),
			"promotion_details": [
				{
					"property": "Designation",
					"current": "Software Developer",
					"new": "Project Manager",
					"fieldname": "designation",
				}
			],
			**values,
		}
	)
	return promotion.insert()
