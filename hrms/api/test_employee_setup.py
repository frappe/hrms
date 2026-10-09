import frappe

from hrms.api.employee_setup import (
	DEMO_EMPLOYEES,
	create_demo_employees,
	create_employees,
	detect_employee_file,
	detect_pasted_employees,
	get_demo_employees,
	get_setup_status,
	import_employees,
	import_pasted_employees,
	normalize_header,
)
from hrms.tests.utils import HRMSTestSuite

COMPANY = "_Test Company"


class TestEmployeeSetup(HRMSTestSuite):
	def setUp(self):
		frappe.set_user("Administrator")
		for email in (
			"setup.manager@example.com",
			"setup.report@example.com",
			"setup.keka1@example.com",
			"setup.keka2@example.com",
		):
			for employee in frappe.get_all("Employee", {"user_id": email}, pluck="name"):
				frappe.delete_doc("Employee", employee, force=True)
			frappe.delete_doc("User", email, force=True, ignore_missing=True)

	def test_setup_status_counts_active_employees(self):
		status = get_setup_status()
		self.assertEqual(status["required"], 3)
		self.assertEqual(status["active_employees"], frappe.db.count("Employee", {"status": "Active"}))
		self.assertIn(COMPANY, status["companies"])

	def test_create_employees_from_rows(self):
		frappe.local.message_log = []
		result = create_employees(
			[
				{
					"employee_name": "Setup Manager",
					"email": "setup.manager@example.com",
					"gender": "F",
					"date_of_birth": "12/04/1990",
					"date_of_joining": "2026-09-01",
					"department": "Setup Dept",
					"designation": "Setup Lead",
				},
				{
					"employee_name": "Setup Report Person",
					"email": "setup.report@example.com",
					"gender": "male",
					"date_of_birth": "1995-01-31",
					"date_of_joining": "01-09-2026",
					"reports_to": "Setup Manager",
				},
				{
					"employee_name": "No Gender",
					"email": "",
					"gender": "",
					"date_of_birth": "1995-01-31",
					"date_of_joining": "2026-09-01",
				},
				{
					"employee_name": "Bad Date",
					"gender": "Male",
					"date_of_birth": "not a date",
					"date_of_joining": "2026-09-01",
				},
			],
			company=COMPANY,
		)

		self.assertEqual(len(result["created"]), 2)
		self.assertEqual(len(result["incomplete"]), 1)
		self.assertEqual(result["incomplete"][0]["missing"], ["Gender"])
		self.assertEqual(len(result["errors"]), 1)
		self.assertIn("Date of Birth", result["errors"][0]["message"])

		manager = frappe.get_doc("Employee", result["created"][0]["name"])
		self.assertEqual(manager.first_name, "Setup")
		self.assertEqual(manager.last_name, "Manager")
		self.assertEqual(manager.gender, "Female")
		self.assertEqual(str(manager.date_of_birth), "1990-04-12")
		self.assertEqual(manager.user_id, "setup.manager@example.com")
		self.assertTrue(frappe.db.exists("User", "setup.manager@example.com"))
		self.assertIn("Employee", frappe.get_roles("setup.manager@example.com"))
		self.assertEqual(frappe.get_message_log(), [])
		self.assertEqual(
			frappe.db.get_value("Department", manager.department, "department_name"), "Setup Dept"
		)
		self.assertEqual(manager.designation, "Setup Lead")

		report = frappe.get_doc("Employee", result["created"][1]["name"])
		self.assertEqual(report.middle_name, "Report")
		self.assertEqual(report.reports_to, manager.name)

	def test_detect_and_import_keka_csv(self):
		content = (
			"Employee Number,Employee Name,Work Email,Gender,Date of Birth,Date of Joining,Department,Job Title,Reporting Manager,Location\n"
			"K1,Keka One,setup.keka1@example.com,Male,1990-05-05,2026-09-01,Sales,Executive,,Kochi\n"
			"K2,Keka Two,setup.keka2@example.com,Female,1992-06-06,2026-09-02,Sales,Executive,Keka One,Kochi\n"
		)
		file_doc = frappe.get_doc(
			{"doctype": "File", "file_name": "keka_export.csv", "content": content, "is_private": 1}
		).insert()

		detected = detect_employee_file(file_doc.file_url)
		self.assertEqual(detected["layout"], "Keka")
		self.assertEqual(detected["row_count"], 2)
		column_map = {c["header"]: c["field"] for c in detected["columns"]}
		self.assertEqual(column_map["Work Email"], "email")
		self.assertEqual(column_map["Job Title"], "designation")
		self.assertEqual(column_map["Reporting Manager"], "reports_to")
		self.assertEqual(column_map["Location"], "")

		result = import_employees(file_doc.file_url, column_map, company=COMPANY)
		self.assertEqual(len(result["created"]), 2)
		self.assertEqual(result["errors"], [])
		two = frappe.get_doc("Employee", result["created"][1]["name"])
		self.assertEqual(two.employee_number, "K2")
		self.assertEqual(two.reports_to, result["created"][0]["name"])

	def test_detect_and_import_pasted_rows(self):
		# copied from a spreadsheet: tab separated, with a blank line above the header
		content = (
			"\n"
			"Full Name\tWork Email\tGender\tDate of Birth\tDate of Joining\tDesignation\n"
			"Keka One\tsetup.keka1@example.com\tMale\t1990-05-05\t2026-09-01\tExecutive\n"
			"Keka Two\tsetup.keka2@example.com\tFemale\t1992-06-06\t2026-09-02\tExecutive\n"
		)
		detected = detect_pasted_employees(content)
		self.assertEqual(detected["row_count"], 2)
		column_map = {c["header"]: c["field"] for c in detected["columns"]}
		self.assertEqual(column_map["Work Email"], "email")
		self.assertEqual(column_map["Designation"], "designation")

		result = import_pasted_employees(content, column_map, company=COMPANY)
		self.assertEqual(result["errors"], [])
		self.assertEqual([r["employee_name"] for r in result["created"]], ["Keka One", "Keka Two"])

		# comma separated text is read as CSV
		detected = detect_pasted_employees("Full Name,Gender\nOnly Name,Male\n")
		self.assertEqual([c["field"] for c in detected["columns"]], ["employee_name", "gender"])
		self.assertEqual(detected["row_count"], 1)

	def test_headerless_paste_guesses_columns_from_values(self):
		content = (
			"Keka One\tsetup.keka1@example.com\tMale\t1990-05-05\t2026-09-01\tSales\tSales Executive\t\n"
			"Keka Two\tsetup.keka2@example.com\tFemale\t1992-06-06\t2026-09-02\tSales\tSales Executive\tKeka One\n"
		)
		detected = detect_pasted_employees(content)
		self.assertFalse(detected["has_header"])
		self.assertEqual(detected["row_count"], 2)
		self.assertEqual(detected["columns"][0]["sample"], "Keka One")
		self.assertEqual(
			[c["field"] for c in detected["columns"]],
			[
				"employee_name",
				"email",
				"gender",
				"date_of_birth",
				"date_of_joining",
				"department",
				"designation",
				"reports_to",
			],
		)

		column_map = {c["header"]: c["field"] for c in detected["columns"]}
		result = import_pasted_employees(content, column_map, company=COMPANY)
		self.assertEqual(result["errors"], [])
		self.assertEqual([r["employee_name"] for r in result["created"]], ["Keka One", "Keka Two"])
		two = frappe.get_doc("Employee", result["created"][1]["name"])
		self.assertEqual(two.reports_to, result["created"][0]["name"])

		# order does not matter, and split names, codes and phone numbers are recognised
		detected = detect_pasted_employees(
			"EMP001,14/03/1988,Ananya,Iyer,F,9876543210,01/08/2024\n"
			"EMP002,22/07/1993,Rohan,Mehta,M,+91 98765 43211,03/06/2024\n"
		)
		self.assertEqual(
			[c["field"] for c in detected["columns"]],
			[
				"employee_number",
				"date_of_birth",
				"first_name",
				"last_name",
				"gender",
				"cell_number",
				"date_of_joining",
			],
		)

	def test_demo_employees(self):
		from frappe.utils import add_months, getdate

		demo = get_demo_employees()
		self.assertEqual([d["employee_name"] for d in demo], [d["employee_name"] for d in DEMO_EMPLOYEES])
		self.assertEqual(
			demo[0]["date_of_joining"], add_months(getdate(), -DEMO_EMPLOYEES[0]["months_since_joining"])
		)
		self.assertNotIn("email", demo[0])

		result = create_demo_employees(company=COMPANY)
		self.assertEqual(result["errors"], [])
		self.assertEqual(result["incomplete"], [])
		self.assertEqual(len(result["created"]), len(DEMO_EMPLOYEES))
		self.assertEqual(result["unresolved_managers"], [])

		by_name = {r["employee_name"]: r["name"] for r in result["created"]}
		engineer = frappe.get_doc("Employee", by_name["Rahul Verma"])
		self.assertEqual(engineer.reports_to, by_name["Priya Nair"])
		self.assertFalse(engineer.user_id)
		self.assertEqual(
			frappe.db.get_value("Department", engineer.department, "department_name"), "Engineering"
		)

	def test_normalize_header(self):
		self.assertEqual(normalize_header(" Date of Joining (DD/MM/YYYY) "), "date of joining")
		self.assertEqual(normalize_header("Work E-mail*"), "work e mail")
