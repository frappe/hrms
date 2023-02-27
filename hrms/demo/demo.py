import frappe

from hrms.demo.employee import EmployeeBatch
from hrms.demo.setup import DemoSetup

"""
1. Setup prerequisites will setup following things
	1.1. Setup wizard
	1.2. Create default roles
	1.3. Create default users
	1.4. Create Payroll Period
	1.5. Create Hotiday List
	1.6. Create Tax Slab

2. Create Employee

3. Create Salary Structure

4. Create Salary Slip via Payroll
"""


def make():
	DemoSetup.prerequisites()


def simulate(number_of_employees: int = 100):
	EmployeeBatch(number_of_employees).process_batch()

	frappe.db.commit()
