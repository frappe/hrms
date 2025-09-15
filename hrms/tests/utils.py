import frappe

from erpnext.tests.utils import ERPNextTestSuite


class HRMSTestSuite(ERPNextTestSuite):
	"""Class for creating HRMS test records"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()

	@classmethod
	def make_employees(cls):
		"""Create test employees"""
		# Create test employees here
		super().make_employees()

	@classmethod
	def make_departments(cls):
		"""Create test departments"""
		# Create test departments here
		records = [
			{
				"doctype": "Department",
				"department_name": "_Test Department",
				"company": "_Test Company",
				"parent_department": "All Departments",
			},
			{
				"doctype": "Department",
				"department_name": "_Test Department 1",
				"company": "_Test Company",
				"parent_department": "All Departments",
			},
		]
		cls.departments = []
		for x in records:
			if not frappe.db.exists("Department", x.get("department_name")):
				cls.departments.append(frappe.get_doc(x).insert())
			else:
				cls.departments.append(frappe.get_doc("Department", x.get("department_name")))

	@classmethod
	def make_leave_types(cls):
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
		cls.leave_types = []
		for x in records:
			if not frappe.db.exists("Leave Type", x.get("leave_type_name")):
				cls.leave_types.append(frappe.get_doc(x).insert())
			else:
				cls.leave_types.append(frappe.get_doc("Leave Type", x.get("leave_type_name")))

	@classmethod
	def make_leave_allocations(cls):
		"""Create test leave applications"""
		# Create test leave applications here
		records = [
			{
				"docstatus": 1,
				"doctype": "Leave Allocation",
				"employee": "_T-Employee-00001",
				"from_date": "2013-01-01",
				"to_date": "2013-12-31",
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

		cls.leave_allocations = []
		for x in records:
			if not frappe.db.exists(
				"Leave Allocation",
				{"employee": x.get("employee"), "from_date": x.get("from_date"), "to_date": x.get("to_date")},
			):
				cls.leave_allocations.append(frappe.get_doc(x).insert())
			else:
				cls.leave_allocations.append(
					frappe.get_doc(
						"Employee",
						{
							"employee": x.get("employee"),
							"from_date": x.get("from_date"),
							"to_date": x.get("to_date"),
						},
					)
				)
