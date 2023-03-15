import random

import frappe
from frappe.model.document import bulk_insert
from frappe.utils.nestedset import rebuild_tree

from hrms.demo.utils import Batch, Date, Log

# from tqdm import tqdm


class DemoEmployee:
	def __init__(self, emp_id):
		self.company = frappe.db.get_single_value("Global Defaults", "default_company")
		self.status = "Active"

		self.set_date_of_birth()
		self.set_date_of_joining()
		self.set_gender()
		self.set_first_name(emp_id)
		self.make_autoname()
		self.set_creation_and_modification_time()
		self.set_owner_and_modified_by()

	def set_date_of_birth(self):
		self.date_of_birth = Date.get_random_date()

	def set_date_of_joining(self):
		self.date_of_joining = Date.add_years(self.date_of_birth, 20)

	def set_gender(self):
		self.gender = random.choice(["Female", "Male", "Other"])

	def set_first_name(self, emp_id: int = 0):
		self.first_name = f"Employee {emp_id}"
		self.employee_name = self.first_name

	def make_autoname(self):
		naming_series = frappe.new_doc("Employee").naming_series
		self.employee = frappe.model.naming.make_autoname(naming_series)
		self.name = self.employee

	def set_creation_and_modification_time(self):
		self.creation = self.modified = frappe.utils.now()

	def set_owner_and_modified_by(self):
		self.owner = self.modified_by = frappe.session.user


class EmployeeBatch(Batch):
	def __init__(self, no_of_records: int = 0):
		super().__init__(
			no_of_records=no_of_records,
			method="hrms.demo.employee.create_employee_records",
			on_success=on_success,
		)

	def process_batch(self):
		self.set_batch()

	@staticmethod
	def create(start, end):
		employees = []
		Log(f"Creating employee records for {start} .. {end}")
		for emp_id in range(start, end):
			employee = DemoEmployee(emp_id)
			employee_doc = frappe.new_doc("Employee")
			employees.append(employee_doc.update(employee.__dict__))

		bulk_insert("Employee", employees, ignore_duplicates=True)
		rebuild_tree("Employee", "reports_to")

	@staticmethod
	def on_success(batch_id):
		Log(f"Completed with batch {batch_id}")


create_employee_records = EmployeeBatch.create
on_success = EmployeeBatch.on_success
