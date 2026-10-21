import frappe
from frappe.utils import add_days, add_months, flt, get_last_day, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_payroll_period,
)
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	create_exemption_declaration,
	create_salary_slips_for_payroll_period,
	create_tax_slab,
	make_earning_salary_component,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	create_salary_structure_assignment,
	make_salary_structure,
)
from hrms.payroll.report.income_tax_computation.income_tax_computation import execute
from hrms.tests.utils import HRMSTestSuite


class TestIncomeTaxComputation(HRMSTestSuite):
	def setUp(self):
		self.cleanup_records()
		self.create_records()

	def cleanup_records(self):
		frappe.qb.from_("Employee Tax Exemption Declaration").delete().run()
		frappe.qb.from_("Payroll Period").delete().run()
		frappe.qb.from_("Income Tax Slab").delete().run()
		frappe.qb.from_("Salary Component").delete().run()
		frappe.qb.from_("Employee Benefit Application").delete().run()
		frappe.qb.from_("Employee Benefit Claim").delete().run()
		employee = frappe.qb.DocType("Employee")
		frappe.qb.from_(employee).delete().where(employee.company == "_Test Company").run()
		frappe.qb.from_("Salary Slip").delete().run()

	def create_records(self):
		self.employee = make_employee(
			"employee_tax_computation@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-10-2021"),
		)

		self.payroll_period = create_payroll_period(name="_Test Payroll Period 1", company="_Test Company")

		self.income_tax_slab = create_tax_slab(
			self.payroll_period,
			allow_tax_exemption=True,
			effective_date=getdate("2019-04-01"),
			company="_Test Company",
		)
		salary_structure = make_salary_structure(
			"Monthly Salary Structure Test Income Tax Computation",
			"Monthly",
			employee=self.employee,
			company="_Test Company",
			currency="INR",
			payroll_period=self.payroll_period,
			test_tax=True,
		)

		create_exemption_declaration(self.employee, self.payroll_period.name)

		create_salary_slips_for_payroll_period(
			self.employee, salary_structure.name, self.payroll_period, deduct_random=False, num=3
		)

	def test_report(self):
		filters = frappe._dict(
			{
				"company": "_Test Company",
				"payroll_period": self.payroll_period.name,
				"employee": self.employee,
			}
		)

		result = execute(filters)

		expected_data = {
			"employee": self.employee,
			"employee_name": "employee_tax_computation@example.com",
			"department": "All Departments",
			"income_tax_slab": self.income_tax_slab,
			"gross_earnings": 936000.0,
			"professional_tax": 2400.0,
			"standard_tax_exemption": 50000,
			"total_exemption": 52400.0,
			"total_taxable_amount": 883600.0,
			"applicable_tax": 92789.0,
			"total_tax_deducted": 17997.0,
			"payable_tax": 74792.0,
		}

		for key, val in expected_data.items():
			self.assertEqual(result[1][0].get(key), val)

		# Run report considering tax exemption declaration
		filters.consider_tax_exemption_declaration = 1

		result = execute(filters)

		expected_data.update(
			{
				"_test_category": 100000.0,
				"total_exemption": 152400.0,
				"total_taxable_amount": 783600.0,
				"applicable_tax": 71989.0,
				"payable_tax": 53992.0,
			}
		)

		for key, val in expected_data.items():
			self.assertEqual(result[1][0].get(key), val)

	def test_employee_joined_after_payroll_period_is_excluded(self):
		# employee joins after the payroll period ends -> employment does not overlap
		# the period, so they must be excluded from the report (and not crash it while
		# trying to build a salary slip with no applicable salary structure)
		joining_date = add_days(self.payroll_period.end_date, 90)
		employee = make_employee(
			"joined_after_period@example.com",
			company="_Test Company",
			date_of_joining=joining_date,
		)
		make_salary_structure(
			"Monthly Salary Structure Joined After Period",
			"Monthly",
			employee=employee,
			company="_Test Company",
			currency="INR",
			from_date=joining_date,
			payroll_period=self.payroll_period,
			test_tax=True,
		)

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"payroll_period": self.payroll_period.name,
			}
		)
		result = execute(filters)[1]

		employees_in_report = [row.get("employee") for row in result]
		self.assertNotIn(employee, employees_in_report)

	def test_employee_relieved_before_payroll_period_is_excluded(self):
		# employee relieved before the payroll period starts -> employment does not
		# overlap the period, so they must be excluded from the report
		joining_date = add_days(self.payroll_period.start_date, -400)
		relieving_date = add_days(self.payroll_period.start_date, -1)
		employee = make_employee(
			"relieved_before_period@example.com",
			company="_Test Company",
			date_of_joining=joining_date,
		)
		make_salary_structure(
			"Monthly Salary Structure Relieved Before Period",
			"Monthly",
			employee=employee,
			company="_Test Company",
			currency="INR",
			from_date=joining_date,
			payroll_period=self.payroll_period,
			test_tax=True,
		)
		frappe.db.set_value("Employee", employee, {"relieving_date": relieving_date, "status": "Left"})

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"payroll_period": self.payroll_period.name,
			}
		)
		result = execute(filters)[1]

		employees_in_report = [row.get("employee") for row in result]
		self.assertNotIn(employee, employees_in_report)

	def test_get_report_for_all_employees(self):
		frappe.db.delete("Employee")
		users = [
			{"email": "test_itrc1@example.com", "args": {"status": "Active"}},
			{"email": "test_itrc2@example.com", "args": {"status": "Inactive"}},
			{"email": "test_itrc3@example.com", "args": {"status": "Suspended"}},
			{"email": "test_itrc4@example.com", "args": {"status": "Left", "relieving_date": getdate()}},
		]

		for user in users:
			employee = make_employee(user["email"], company="_Test Company")
			salary_structure = make_salary_structure(
				"Monthly Salary Structure Test Income Tax Computation",
				"Monthly",
				employee=employee,
				company="_Test Company",
				currency="INR",
				payroll_period=self.payroll_period,
				test_tax=True,
			)

			create_salary_slips_for_payroll_period(
				employee, salary_structure.name, self.payroll_period, deduct_random=False, num=3
			)
			frappe.db.set_value("Employee", employee, user["args"])

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"payroll_period": self.payroll_period.name,
			}
		)
		result = execute(filters)[1]
		self.assertEqual(len(result), 4)

	def get_report_row(self, employee, **filters):
		result = execute(
			frappe._dict(
				{
					"company": "_Test Company",
					"payroll_period": self.payroll_period.name,
					"employee": employee,
					**filters,
				}
			)
		)
		return result[1][0]

	def get_expected_taxable_amount(self, salary_slip, row):
		return (
			flt(salary_slip.annual_taxable_amount)
			+ flt(salary_slip.tax_exemption_declaration)
			+ flt(salary_slip.standard_tax_exemption_amount)
			+ flt(salary_slip.deductions_before_tax_calculation)
			- flt(row.get("professional_tax"))
			- flt(row.get("standard_tax_exemption"))
		)

	def test_non_taxable_earnings_are_not_subtracted_twice(self):
		employee = make_employee(
			"non_taxable_tax_computation@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-10-2021"),
		)
		earnings = make_earning_salary_component(setup=True, test_tax=True, company_list=["_Test Company"])
		for earning in earnings:
			if earning["salary_component"] == "HRA":
				earning["is_tax_applicable"] = 0
		frappe.db.set_value("Salary Component", "HRA", "is_tax_applicable", 0)

		salary_structure = make_salary_structure(
			"Monthly Salary Structure Non Taxable Income Tax Computation",
			"Monthly",
			employee=employee,
			company="_Test Company",
			currency="INR",
			payroll_period=self.payroll_period,
			test_tax=True,
			earnings=earnings,
		)
		create_salary_slips_for_payroll_period(
			employee, salary_structure.name, self.payroll_period, deduct_random=False, num=1
		)
		next_slip = make_salary_slip(
			salary_structure.name,
			employee=employee,
			posting_date=get_last_day(add_months(self.payroll_period.start_date, 1)),
		)

		row = self.get_report_row(employee)
		self.assertEqual(row["hra"], 36000)
		self.assertEqual(row["total_taxable_amount"], self.get_expected_taxable_amount(next_slip, row))

	def test_standard_exemption_of_slab_from_another_company(self):
		expected = self.get_report_row(self.employee)
		frappe.db.set_value("Income Tax Slab", self.income_tax_slab, "company", "_Test Company 1")

		row = self.get_report_row(self.employee)
		self.assertEqual(row["standard_tax_exemption"], 50000)
		self.assertEqual(row["total_taxable_amount"], expected["total_taxable_amount"])

	def test_assignment_from_next_payroll_period_is_ignored(self):
		expected = self.get_report_row(self.employee)

		salary_structure = frappe.db.get_value(
			"Salary Structure Assignment", {"employee": self.employee, "docstatus": 1}, "salary_structure"
		)
		next_assignment = create_salary_structure_assignment(
			self.employee,
			salary_structure,
			from_date=add_days(self.payroll_period.end_date, 1),
			company="_Test Company",
			payroll_period=self.payroll_period,
			allow_duplicate=True,
		)
		next_assignment.db_set("taxable_earnings_till_date", 999999)

		row = self.get_report_row(self.employee)
		self.assertEqual(row["gross_earnings"], expected["gross_earnings"])
		self.assertEqual(row["total_taxable_amount"], expected["total_taxable_amount"])

	def test_opening_values_from_earliest_assignment_in_period(self):
		employee = make_employee(
			"opening_tax_computation@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-10-2021"),
		)
		salary_structure = make_salary_structure(
			"Monthly Salary Structure Opening Income Tax Computation",
			"Monthly",
			employee=employee,
			company="_Test Company",
			currency="INR",
			payroll_period=self.payroll_period,
			test_tax=True,
		)
		first_assignment = frappe.get_last_doc("Salary Structure Assignment", {"employee": employee})
		first_assignment.db_set({"taxable_earnings_till_date": 100000, "tax_deducted_till_date": 10000})
		create_salary_structure_assignment(
			employee,
			salary_structure.name,
			from_date=add_months(self.payroll_period.start_date, 6),
			company="_Test Company",
			payroll_period=self.payroll_period,
			allow_duplicate=True,
		)

		row = self.get_report_row(employee)
		self.assertEqual(row["total_tax_deducted"], 10000)

	def test_mid_period_joiner_without_salary_slip(self):
		joining_date = add_months(self.payroll_period.start_date, 5)
		employee = make_employee(
			"mid_period_joiner_tax_computation@example.com",
			company="_Test Company",
			date_of_joining=joining_date,
		)
		salary_structure = make_salary_structure(
			"Monthly Salary Structure Mid Period Income Tax Computation",
			"Monthly",
			employee=employee,
			company="_Test Company",
			currency="INR",
			from_date=joining_date,
			payroll_period=self.payroll_period,
			test_tax=True,
		)
		frappe.get_last_doc("Salary Structure Assignment", {"employee": employee}).db_set(
			{"taxable_earnings_till_date": 200000, "tax_deducted_till_date": 20000}
		)
		first_slip = make_salary_slip(
			salary_structure.name, employee=employee, posting_date=get_last_day(joining_date)
		)

		row = self.get_report_row(employee)
		self.assertTrue(row["total_taxable_amount"])
		self.assertEqual(row["total_taxable_amount"], self.get_expected_taxable_amount(first_slip, row))
		self.assertEqual(row["total_tax_deducted"], 20000)

	def test_mid_period_go_live_does_not_break_report(self):
		employee = make_employee(
			"go_live_tax_computation@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-10-2021"),
		)
		make_salary_structure(
			"Monthly Salary Structure Go Live Income Tax Computation",
			"Monthly",
			employee=employee,
			company="_Test Company",
			currency="INR",
			from_date=add_months(self.payroll_period.start_date, 6),
			payroll_period=self.payroll_period,
			test_tax=True,
		)

		result = execute(
			frappe._dict({"company": "_Test Company", "payroll_period": self.payroll_period.name})
		)[1]
		row = next(row for row in result if row["employee"] == employee)
		self.assertTrue(row["total_taxable_amount"])

	def test_relieved_employee_uses_last_salary_slip(self):
		last_slip = frappe.get_last_doc(
			"Salary Slip", {"employee": self.employee, "docstatus": 1}, order_by="end_date desc"
		)
		frappe.db.set_value("Employee", self.employee, "relieving_date", last_slip.end_date)

		row = self.get_report_row(self.employee)
		self.assertTrue(row["total_taxable_amount"])
		self.assertEqual(row["total_taxable_amount"], self.get_expected_taxable_amount(last_slip, row))

	def test_employee_status_filter_with_department(self):
		frappe.db.set_value(
			"Employee", self.employee, {"department": "_Test Department - _TC", "status": "Left"}
		)

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"payroll_period": self.payroll_period.name,
				"department": "_Test Department - _TC",
				"employee_status": "Active",
			}
		)
		self.assertRaises(frappe.ValidationError, execute, filters)

	def test_amounts_in_salary_slip_currency(self):
		expected = self.get_report_row(self.employee)
		for slip in frappe.get_all("Salary Slip", {"employee": self.employee, "docstatus": 1}, pluck="name"):
			gross_pay = frappe.db.get_value("Salary Slip", slip, "gross_pay")
			frappe.db.set_value(
				"Salary Slip", slip, {"exchange_rate": 80, "base_gross_pay": flt(gross_pay) * 80}
			)

		columns, data = execute(
			frappe._dict(
				{
					"company": "_Test Company",
					"payroll_period": self.payroll_period.name,
					"employee": self.employee,
				}
			)
		)
		row = data[0]
		self.assertEqual(row["currency"], "INR")
		self.assertEqual(row["gross_earnings"], expected["gross_earnings"])
		self.assertEqual(row["total_tax_deducted"], expected["total_tax_deducted"])

		currency_columns = [col for col in columns if col["fieldtype"] == "Currency"]
		self.assertTrue(currency_columns)
		for col in currency_columns:
			self.assertEqual(col["options"], "currency")
