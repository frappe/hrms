# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class VehicleLog(Document):
	def validate(self):
		if flt(self.odometer) < flt(self.last_odometer):
			frappe.throw(
				_("Current Odometer Value should be greater than Last Odometer Value {0}").format(
					self.last_odometer
				)
			)

	def on_submit(self):
		frappe.db.set_value("Vehicle", self.license_plate, "last_odometer", self.odometer)

	def before_cancel(self):
		for expense_claim_name in _get_draft_expense_claims(self.name):
			expense_claim = frappe.get_doc("Expense Claim", expense_claim_name)

			if _has_non_vehicle_log_expenses(expense_claim):
				for row in list(expense_claim.expenses):
					if row.description == _("Vehicle Expenses"):
						expense_claim.remove(row)

				expense_claim.vehicle_log = None
				expense_claim.save()
			else:
				expense_claim.delete()

	def on_cancel(self):
		distance_travelled = self.odometer - self.last_odometer
		if distance_travelled > 0:
			updated_odometer_value = (
				int(frappe.db.get_value("Vehicle", self.license_plate, "last_odometer")) - distance_travelled
			)
			frappe.db.set_value("Vehicle", self.license_plate, "last_odometer", updated_odometer_value)


@frappe.whitelist()
def make_expense_claim(docname: str) -> dict:
	frappe.has_permission("Vehicle Log", "read", docname, throw=True)

	expense_claim = frappe.db.exists("Expense Claim", {"vehicle_log": docname})
	if expense_claim:
		frappe.throw(_("Expense Claim {0} already exists for the Vehicle Log").format(expense_claim))

	vehicle_log = frappe.get_doc("Vehicle Log", docname)
	service_expense = sum([flt(d.expense_amount) for d in vehicle_log.service_detail])
	refuelling_expense = flt(vehicle_log.price) * flt(vehicle_log.fuel_qty)
	claim_amount = service_expense + refuelling_expense
	if not claim_amount:
		frappe.throw(_("No additional expenses has been added"))

	exp_claim = frappe.new_doc("Expense Claim")
	exp_claim.employee = vehicle_log.employee
	exp_claim.vehicle_log = vehicle_log.name
	exp_claim.remark = _("Expense Claim for Vehicle Log {0}").format(vehicle_log.name)
	exp_claim.append(
		"expenses",
		{"expense_date": vehicle_log.date, "description": _("Vehicle Expenses"), "amount": claim_amount},
	)
	return exp_claim.as_dict()


@frappe.whitelist()
def get_draft_expense_claims(vehicle_log: str) -> list[str]:
	frappe.has_permission("Vehicle Log", doc=vehicle_log, throw=True)

	return _get_draft_expense_claims(vehicle_log)


@frappe.whitelist()
def get_draft_expense_claim_cancellation_actions(vehicle_log: str) -> list[dict[str, str]]:
	frappe.has_permission("Vehicle Log", doc=vehicle_log, throw=True)

	return [
		{
			"name": expense_claim.name,
			"action": "unlink" if _has_non_vehicle_log_expenses(expense_claim) else "delete",
		}
		for expense_claim in _get_draft_expense_claim_docs(vehicle_log)
	]


def _get_draft_expense_claims(vehicle_log: str) -> list[str]:
	return frappe.get_all(
		"Expense Claim",
		filters={"vehicle_log": vehicle_log, "docstatus": 0},
		pluck="name",
		order_by="creation asc",
	)


def _get_draft_expense_claim_docs(vehicle_log: str) -> list[Document]:
	return [
		frappe.get_doc("Expense Claim", expense_claim_name)
		for expense_claim_name in _get_draft_expense_claims(vehicle_log)
	]


def _has_non_vehicle_log_expenses(expense_claim: Document) -> bool:
	vehicle_log_description = _("Vehicle Expenses")
	return any(row.description != vehicle_log_description for row in expense_claim.expenses)
