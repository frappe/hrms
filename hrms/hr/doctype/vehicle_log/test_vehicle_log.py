# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.desk.form.linked_with import cancel_all_linked_docs, get_submitted_linked_docs
from frappe.utils import cstr, flt, nowdate, random_string

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.vehicle_log.vehicle_log import (
	get_draft_expense_claim_cancellation_actions,
	get_draft_expense_claims,
	make_expense_claim,
)
from hrms.tests.utils import HRMSTestSuite


class TestVehicleLog(HRMSTestSuite):
	def setUp(self):
		employee_id = frappe.db.sql("""select name from `tabEmployee` where name='testdriver@example.com'""")
		self.employee_id = employee_id[0][0] if employee_id else None

		if not self.employee_id:
			self.employee_id = make_employee("testdriver@example.com", company="_Test Company")

		self.license_plate = get_vehicle(self.employee_id)

	def test_make_vehicle_log_and_syncing_of_odometer_value(self):
		vehicle_log = make_vehicle_log(self.license_plate, self.employee_id)

		# checking value of vehicle odometer value on submit.
		vehicle = frappe.get_doc("Vehicle", self.license_plate)
		self.assertEqual(vehicle.last_odometer, vehicle_log.odometer)

		# checking value vehicle odometer on vehicle log cancellation.
		last_odometer = vehicle_log.last_odometer
		current_odometer = vehicle_log.odometer
		distance_travelled = current_odometer - last_odometer

		vehicle_log.cancel()
		vehicle.reload()

		self.assertEqual(vehicle.last_odometer, current_odometer - distance_travelled)

		vehicle_log.delete()

	def test_vehicle_log_fuel_expense(self):
		vehicle_log = make_vehicle_log(self.license_plate, self.employee_id)

		expense_claim = make_expense_claim(vehicle_log.name)
		fuel_expense = expense_claim.expenses[0].amount
		self.assertEqual(fuel_expense, 50 * 500)

		vehicle_log.cancel()
		frappe.delete_doc("Vehicle Log", vehicle_log.name)

	def test_vehicle_log_with_service_expenses(self):
		vehicle_log = make_vehicle_log(self.license_plate, self.employee_id, with_services=True)

		expense_claim = make_expense_claim(vehicle_log.name)
		expenses = expense_claim.expenses[0].amount
		self.assertEqual(expenses, 27000)

		vehicle_log.cancel()
		frappe.delete_doc("Vehicle Log", vehicle_log.name)

	def test_cancel_vehicle_log_unlinks_draft_expense_claim(self):
		vehicle_log = make_vehicle_log(self.license_plate, self.employee_id)
		currency, cost_center = frappe.db.get_value(
			"Company", "_Test Company", ["default_currency", "cost_center"]
		)
		expense_claim = frappe.get_doc(
			{
				"doctype": "Expense Claim",
				"employee": self.employee_id,
				"company": "_Test Company",
				"currency": currency,
				"exchange_rate": 1,
				"approval_status": "Approved",
				"payable_account": frappe.db.get_value("Company", "_Test Company", "default_payable_account"),
				"vehicle_log": vehicle_log.name,
				"expenses": [
					{
						"expense_type": "Travel",
						"default_account": "Travel Expenses - _TC",
						"currency": currency,
						"amount": 100,
						"sanctioned_amount": 100,
						"cost_center": cost_center,
					}
				],
			}
		).insert()

		self.assertIn(expense_claim.name, get_draft_expense_claims(vehicle_log.name))
		self.assertEqual(
			get_draft_expense_claim_cancellation_actions(vehicle_log.name),
			[{"name": expense_claim.name, "action": "unlink"}],
		)

		vehicle_log.reload()
		vehicle_log.cancel()
		expense_claim.reload()

		self.assertEqual(vehicle_log.docstatus, 2)
		self.assertIsNone(expense_claim.vehicle_log)
		self.assertNotIn(expense_claim.name, get_draft_expense_claims(vehicle_log.name))
		# non-Vehicle-Log expense rows remain intact
		self.assertEqual(len(expense_claim.expenses), 1)
		self.assertEqual(expense_claim.expenses[0].expense_type, "Travel")

		expense_claim.submit()

		expense_claim.cancel()
		frappe.delete_doc("Vehicle Log", vehicle_log.name)

	def test_cancel_vehicle_log_deletes_claim_with_only_vehicle_log_expenses(self):
		vehicle_log = make_vehicle_log(self.license_plate, self.employee_id)
		currency, cost_center = frappe.db.get_value(
			"Company", "_Test Company", ["default_currency", "cost_center"]
		)

		expense_claim = frappe.get_doc(
			{
				"doctype": "Expense Claim",
				"employee": self.employee_id,
				"company": "_Test Company",
				"currency": currency,
				"exchange_rate": 1,
				"approval_status": "Approved",
				"payable_account": frappe.db.get_value("Company", "_Test Company", "default_payable_account"),
				"vehicle_log": vehicle_log.name,
				"expenses": [
					{
						"expense_date": nowdate(),
						"expense_type": "Travel",
						"default_account": "Travel Expenses - _TC",
						"currency": currency,
						"description": "Vehicle Expenses",
						"amount": 25000,
						"sanctioned_amount": 25000,
						"cost_center": cost_center,
					}
				],
			}
		).insert()

		self.assertIn(expense_claim.name, get_draft_expense_claims(vehicle_log.name))
		self.assertEqual(
			get_draft_expense_claim_cancellation_actions(vehicle_log.name),
			[{"name": expense_claim.name, "action": "delete"}],
		)

		vehicle_log.reload()
		vehicle_log.cancel()

		self.assertFalse(frappe.db.exists("Expense Claim", expense_claim.name))
		frappe.delete_doc("Vehicle Log", vehicle_log.name)

	def test_cancel_vehicle_log_removes_only_vehicle_log_rows_from_mixed_claim(self):
		vehicle_log = make_vehicle_log(self.license_plate, self.employee_id)
		currency, cost_center = frappe.db.get_value(
			"Company", "_Test Company", ["default_currency", "cost_center"]
		)

		expense_claim = frappe.get_doc(
			{
				"doctype": "Expense Claim",
				"employee": self.employee_id,
				"company": "_Test Company",
				"currency": currency,
				"exchange_rate": 1,
				"approval_status": "Approved",
				"payable_account": frappe.db.get_value("Company", "_Test Company", "default_payable_account"),
				"vehicle_log": vehicle_log.name,
				"expenses": [
					{
						"expense_date": nowdate(),
						"expense_type": "Travel",
						"default_account": "Travel Expenses - _TC",
						"currency": currency,
						"description": "Vehicle Expenses",
						"amount": 25000,
						"sanctioned_amount": 25000,
						"cost_center": cost_center,
					},
					{
						"expense_date": nowdate(),
						"expense_type": "Travel",
						"default_account": "Travel Expenses - _TC",
						"currency": currency,
						"description": "Accident Repair",
						"amount": 5000,
						"sanctioned_amount": 5000,
						"cost_center": cost_center,
					},
				],
			}
		).insert()

		self.assertIn(expense_claim.name, get_draft_expense_claims(vehicle_log.name))
		self.assertEqual(len(expense_claim.expenses), 2)
		self.assertEqual(
			get_draft_expense_claim_cancellation_actions(vehicle_log.name),
			[{"name": expense_claim.name, "action": "unlink"}],
		)

		vehicle_log.reload()
		vehicle_log.cancel()

		expense_claim.reload()
		self.assertEqual(len(expense_claim.expenses), 1)
		self.assertEqual(expense_claim.expenses[0].description, "Accident Repair")
		self.assertIsNone(expense_claim.vehicle_log)

		expense_claim.submit()
		expense_claim.cancel()
		frappe.delete_doc("Vehicle Log", vehicle_log.name)

	def test_cancel_vehicle_log_with_submitted_expense_claim_uses_linked_doc_cancellation(self):
		vehicle_log = make_vehicle_log(self.license_plate, self.employee_id)
		currency, cost_center = frappe.db.get_value(
			"Company", "_Test Company", ["default_currency", "cost_center"]
		)
		expense_claim = frappe.get_doc(
			{
				"doctype": "Expense Claim",
				"employee": self.employee_id,
				"company": "_Test Company",
				"currency": currency,
				"exchange_rate": 1,
				"approval_status": "Approved",
				"payable_account": frappe.db.get_value("Company", "_Test Company", "default_payable_account"),
				"vehicle_log": vehicle_log.name,
				"expenses": [
					{
						"expense_type": "Travel",
						"default_account": "Travel Expenses - _TC",
						"currency": currency,
						"amount": 100,
						"sanctioned_amount": 100,
						"cost_center": cost_center,
					}
				],
			}
		).insert()
		expense_claim.submit()

		linked_docs = get_submitted_linked_docs("Vehicle Log", vehicle_log.name)["docs"]
		self.assertIn({"doctype": "Expense Claim", "name": expense_claim.name, "docstatus": 1}, linked_docs)

		cancel_all_linked_docs(json.dumps(linked_docs))
		expense_claim.reload()
		self.assertEqual(expense_claim.docstatus, 2)

		vehicle_log.reload()
		vehicle_log.cancel()
		self.assertEqual(vehicle_log.docstatus, 2)


def get_vehicle(employee_id):
	license_plate = random_string(10).upper()
	vehicle = frappe.get_doc(
		{
			"doctype": "Vehicle",
			"license_plate": cstr(license_plate),
			"make": "Maruti",
			"model": "PCM",
			"employee": employee_id,
			"last_odometer": 5000,
			"acquisition_date": nowdate(),
			"location": "Mumbai",
			"chassis_no": "1234ABCD",
			"uom": "Litre",
			"vehicle_value": flt(500000),
		}
	)
	try:
		vehicle.insert(ignore_if_duplicate=True)
	except frappe.DuplicateEntryError:
		pass
	return license_plate


def make_vehicle_log(license_plate, employee_id, with_services=False):
	vehicle_log = frappe.get_doc(
		{
			"doctype": "Vehicle Log",
			"license_plate": cstr(license_plate),
			"employee": employee_id,
			"date": nowdate(),
			"odometer": 5010,
			"fuel_qty": flt(50),
			"price": flt(500),
		}
	)

	if with_services:
		vehicle_log.append(
			"service_detail",
			{
				"service_item": "Oil Change",
				"type": "Inspection",
				"frequency": "Mileage",
				"expense_amount": flt(500),
			},
		)
		vehicle_log.append(
			"service_detail",
			{
				"service_item": "Wheels",
				"type": "Change",
				"frequency": "Half Yearly",
				"expense_amount": flt(1500),
			},
		)

	vehicle_log.save()
	vehicle_log.submit()

	return vehicle_log
