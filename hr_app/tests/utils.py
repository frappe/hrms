import frappe
from frappe.utils import getdate

from erpnext.accounts.utils import get_fiscal_year
from erpnext.tests.utils import ERPNextTestSuite


class BootStrapTestData:
	def __init__(self):
		self.make_presets()
		self.make_master_data()

	def make_presets(self):
		self.make_designations()

	def make_master_data(self):
		self.make_company()
		self.make_exchange_rate()
		self.make_holiday_list()
		self.make_holiday_list_assignment()
		self.make_leave_types()
		self.make_leave_period()
		self.make_leave_block_lists()
		self.make_leave_allocations()
		self.make_leave_applications()
		self.make_salary_components()
		self.update_email_account_settings()
		self.update_system_settings()
		# TODO: clean up
		if frappe.db.get_value("Holiday List Assignment", {"assigned_to": "_Test Company"}, "docstatus") == 0:
			frappe.get_doc("Holiday List Assignment", {"assigned_to": "_Test Company"}).submit()
		frappe.db.commit()  # nosemgrep

	def make_designations(self):
		designations = [
			"Engineer",
			"Project Manager",
			"Researcher",
			"Accountant",
			"Manager",
			"Software Developer",
			"UX Designer",
			"Designer",
		]
		records = [{"doctype": "Designation", "designation_name": x} for x in designations]
		self.make_records(["designation_name"], records)

	def make_exchange_rate(self):
		records = [
			{
				"doctype": "Currency Exchange",
				"date": "2016-01-01",
				"exchange_rate": 60.0,
				"from_currency": "USD",
				"to_currency": "INR",
				"for_buying": 1,
				"for_selling": 0,
			},
			{
				"doctype": "Currency Exchange",
				"date": "2016-01-10",
				"exchange_rate": 65.1,
				"from_currency": "USD",
				"to_currency": "INR",
				"for_buying": 1,
				"for_selling": 0,
			},
			{
				"doctype": "Currency Exchange",
				"date": "2016-01-30",
				"exchange_rate": 62.9,
				"from_currency": "USD",
				"to_currency": "INR",
				"for_buying": 1,
				"for_selling": 1,
			},
		]
		self.make_records(["date", "from_currency", "to_currency"], records)

	def make_salary_components(self):
		records = [
			{
				"doctype": "Salary Component",
				"salary_component": "_Test Basic Salary",
				"type": "Earning",
				"is_tax_applicable": 1,
			},
			{
				"doctype": "Salary Component",
				"salary_component": "_Test Allowance",
				"type": "Earning",
				"is_tax_applicable": 1,
			},
			{
				"doctype": "Salary Component",
				"salary_component": "_Test Professional Tax",
				"type": "Deduction",
			},
			{"doctype": "Salary Component", "salary_component": "_Test TDS", "type": "Deduction"},
			{
				"doctype": "Salary Component",
				"salary_component": "Basic",
				"type": "Earning",
				"is_tax_applicable": 1,
			},
			{
				"doctype": "Salary Component",
				"salary_component": "Leave Encashment",
				"type": "Earning",
				"is_tax_applicable": 1,
			},
		]
		self.make_records(["salary_component"], records)

	def make_company(self):
		records = [
			{
				"abbr": "_TC",
				"company_name": "_Test Company",
				"country": "India",
				"default_currency": "INR",
				"doctype": "Company",
				"chart_of_accounts": "Standard",
			}
		]
		self.make_records(["company_name"], records)

	def make_holiday_list_assignment(self):
		fiscal_year = get_fiscal_year(getdate())
		records = [
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": "_Test Company",
				"holiday_list": "Salary Slip Test Holiday List",
				"from_date": fiscal_year[1],
				"to_date": fiscal_year[2],
			}
		]
		self.make_records(["assigned_to", "from_date"], records)

	def make_holiday_list(self):
		fiscal_year = get_fiscal_year(getdate())
		records = [
			{
				"doctype": "Holiday List",
				"from_date": fiscal_year[1],
				"to_date": fiscal_year[2],
				"holiday_list_name": "Salary Slip Test Holiday List",
				"weekly_off": "Sunday",
			}
		]
		self.make_records(["from_date", "to_date", "holiday_list_name"], records)

	def make_leave_types(self):
		"""Create test leave types"""
		# Create test leave types here
		records = [
			{"doctype": "Leave Type", "leave_type_name": "_Test Leave Type", "include_holiday": 1},
			{
				"doctype": "Leave Type",
				"is_lwp": 1,
				"leave_type_name": "_Test Leave Type LWP",
				"include_holiday": 1,
			},
			{
				"doctype": "Leave Type",
				"leave_type_name": "_Test Leave Type Encashment",
				"include_holiday": 1,
				"allow_encashment": 1,
				"non_encashable_leaves": 5,
				"earning_component": "Leave Encashment",
			},
			{
				"doctype": "Leave Type",
				"leave_type_name": "_Test Leave Type Earned",
				"include_holiday": 1,
				"is_earned_leave": 1,
			},
		]
		self.make_records(["leave_type_name"], records)

	def make_leave_period(self):
		records = [
			{
				"doctype": "Leave Period",
				"company": "_Test Company",
				"from_date": "2013-01-01",
				"to_date": "2019-12-31",
			}
		]
		self.make_records(["from_date", "to_date", "company"], records)

	def make_leave_allocations(self):
		"""Create test leave applications"""
		# Create test leave applications here
		records = [
			{
				"docstatus": 1,
				"doctype": "Leave Allocation",
				"employee": "_T-Employee-00001",
				"from_date": "2013-01-01",
				"to_date": "2019-12-31",
				"leave_type": "_Test Leave Type",
				"new_leaves_allocated": 15,
			},
			{
				"docstatus": 1,
				"doctype": "Leave Allocation",
				"employee": "_T-Employee-00002",
				"from_date": "2013-01-01",
				"to_date": "2013-12-31",
				"leave_type": "_Test Leave Type",
				"new_leaves_allocated": 15,
			},
		]
		self.make_records(["employee", "from_date", "to_date"], records)

	def make_leave_applications(self):
		records = [
			{
				"company": "_Test Company",
				"doctype": "Leave Application",
				"employee": "_T-Employee-00001",
				"from_date": "2013-05-01",
				"description": "_Test Reason",
				"leave_type": "_Test Leave Type",
				"posting_date": "2013-01-02",
				"to_date": "2013-05-05",
			},
			{
				"company": "_Test Company",
				"doctype": "Leave Application",
				"employee": "_T-Employee-00002",
				"from_date": "2013-05-01",
				"description": "_Test Reason",
				"leave_type": "_Test Leave Type",
				"posting_date": "2013-01-02",
				"to_date": "2013-05-05",
			},
			{
				"company": "_Test Company",
				"doctype": "Leave Application",
				"employee": "_T-Employee-00001",
				"from_date": "2013-01-15",
				"description": "_Test Reason",
				"leave_type": "_Test Leave Type LWP",
				"posting_date": "2013-01-02",
				"to_date": "2013-01-15",
			},
		]
		self.make_records(["employee", "from_date"], records)

	def make_leave_block_lists(self):
		records = [
			{
				"company": "_Test Company",
				"doctype": "Leave Block List",
				"leave_block_list_allowed": [
					{
						"allow_user": "test1@example.com",
						"doctype": "Leave Block List Allow",
						"parent": "_Test Leave Block List",
						"parentfield": "leave_block_list_allowed",
						"parenttype": "Leave Block List",
					}
				],
				"leave_block_list_dates": [
					{
						"block_date": "2013-01-02",
						"doctype": "Leave Block List Date",
						"parent": "_Test Leave Block List",
						"parentfield": "leave_block_list_dates",
						"parenttype": "Leave Block List",
						"reason": "First work day",
					}
				],
				"leave_block_list_name": "_Test Leave Block List",
				"year": "_Test Fiscal Year 2013",
				"applies_to_all_departments": 1,
			},
			{
				"company": "_Test Company",
				"doctype": "Leave Block List",
				"leave_type": "Casual Leave",
				"leave_block_list_allowed": [
					{
						"allow_user": "test1@example.com",
						"doctype": "Leave Block List Allow",
						"parent": "_Test Leave Block List Casual Leave 1",
						"parentfield": "leave_block_list_allowed",
						"parenttype": "Leave Block List",
					}
				],
				"leave_block_list_dates": [
					{
						"block_date": "2013-01-16",
						"doctype": "Leave Block List Date",
						"parent": "_Test Leave Block List Casual Leave 1",
						"parentfield": "leave_block_list_dates",
						"parenttype": "Leave Block List",
						"reason": "First work day",
					}
				],
				"leave_block_list_name": "_Test Leave Block List Casual Leave 1",
				"year": "_Test Fiscal Year 2013",
				"applies_to_all_departments": 1,
			},
			{
				"company": "_Test Company",
				"doctype": "Leave Block List",
				"leave_type": "Casual Leave",
				"leave_block_list_allowed": [],
				"leave_block_list_dates": [
					{
						"block_date": "2013-01-19",
						"doctype": "Leave Block List Date",
						"parent": "_Test Leave Block List Casual Leave 2",
						"parentfield": "leave_block_list_dates",
						"parenttype": "Leave Block List",
						"reason": "First work day",
					}
				],
				"leave_block_list_name": "_Test Leave Block List Casual Leave 2",
				"year": "_Test Fiscal Year 2013",
				"applies_to_all_departments": 1,
			},
		]
		self.make_records(["leave_block_list_name"], records)

	def update_email_account_settings(self):
		email_account = frappe.get_doc("Email Account", "Jobs")
		email_account.enable_outgoing = 1
		email_account.default_outgoing = 1
		email_account.save()

	def update_system_settings(self):
		system_settings = frappe.get_doc("System Settings")
		system_settings.country = "India"
		system_settings.save()

	def make_records(self, key, records):
		doctype = records[0].get("doctype")

		def get_filters(record):
			filters = {}
			for x in key:
				filters[x] = record.get(x)
			return filters

		for x in records:
			filters = get_filters(x)
			if not frappe.db.exists(doctype, filters):
				doc = frappe.get_doc(x).insert()
				if doctype == "Holiday List":
					doc.get_weekly_off_dates()
					doc.save()


BootStrapTestData()


class HRMSTestSuite(ERPNextTestSuite):
	"""Class for creating HRMS test records"""

	pass
