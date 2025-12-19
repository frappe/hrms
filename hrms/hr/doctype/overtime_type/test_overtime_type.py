# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

# import frappe
import frappe
from frappe.tests import UnitTestCase

from hrms.payroll.doctype.salary_slip.test_salary_slip import make_salary_component


class TestOvertimeType(UnitTestCase):
	"""
	Unit tests for OvertimeType.
	Use this class for testing individual functions and methods.
	"""

	pass


def create_overtime_type(**args):
	args = frappe._dict(args)

	overtime_type = frappe.new_doc("Overtime Type")
	overtime_type.name = args.get("name") or "_Test Overtime"
	overtime_type.overtime_calculation_method = args.overtime_calculation_method or "Salary Component Based"
	overtime_type.standard_multiplier = 1
	overtime_type.applicable_for_weekend = args.applicable_for_weekend or 0
	overtime_type.applicable_for_public_holiday = args.applicable_for_public_holiday or 0
	overtime_type.maximum_overtime_hours_allowed = args.maximum_overtime_hours_allowed or 0
	overtime_type.overtime_salary_component = args.overtime_salary_component or "Overtime"

	if overtime_type.overtime_calculation_method == "Fixed Hourly Rate":
		overtime_type.hourly_rate = 400
	elif overtime_type.overtime_calculation_method == "Salary Component Based":
		overtime_type.append("applicable_salary_component", {"salary_component": "Basic Salary"})

	if args.applicable_for_weekend:
		overtime_type.weekend_multiplier = 1.5
	if args.applicable_for_public_holidays:
		overtime_type.public_holiday_multiplier = 2

	overtime_type.save()

	return overtime_type
