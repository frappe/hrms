# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import flt, get_link_to_form, today

from hrms.hr.doctype.expense_claim.expense_claim import get_outstanding_amount_for_claim
from hrms.hr.doctype.full_and_final_statement.full_and_final_statement_loan_utils import (
	cancel_loan_repayment,
	process_loan_accrual,
)

OUTSTANDING_REFERENCE_DOCTYPES = ("Expense Claim", "Gratuity", "Leave Encashment", "Employee Advance")


class FullandFinalStatement(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.full_and_final_asset.full_and_final_asset import FullandFinalAsset
		from hrms.hr.doctype.full_and_final_outstanding_statement.full_and_final_outstanding_statement import (
			FullandFinalOutstandingStatement,
		)

		amended_from: DF.Link | None
		assets_allocated: DF.Table[FullandFinalAsset]
		company: DF.Link | None
		date_of_joining: DF.Date | None
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		payables: DF.Table[FullandFinalOutstandingStatement]
		receivables: DF.Table[FullandFinalOutstandingStatement]
		relieving_date: DF.Date | None
		status: DF.Literal["Paid", "Unpaid", "Cancelled"]
		total_asset_recovery_cost: DF.Currency
		total_payable_amount: DF.Currency
		total_receivable_amount: DF.Currency
		transaction_date: DF.Date
	# end: auto-generated types

	def before_insert(self):
		self.status = "Unpaid"
		self.get_outstanding_statements()

	def validate(self):
		self.validate_relieving_date()
		self.validate_reference_documents()
		self.get_assets_statements()
		self.set_total_asset_recovery_cost()
		self.set_totals()

	def before_submit(self):
		self.validate_settlement("payables")
		self.validate_settlement("receivables")
		self.validate_assets()

	def on_submit(self):
		process_loan_accrual(self)

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry",)
		cancel_loan_repayment(self)

	def on_discard(self):
		self.db_set("status", "Cancelled")

	def validate_relieving_date(self):
		if not self.relieving_date:
			frappe.throw(
				_("Please set {0} for Employee {1}").format(
					frappe.bold(_("Relieving Date")),
					get_link_to_form("Employee", self.employee),
				),
				title=_("Missing Relieving Date"),
			)

	def validate_reference_documents(self):
		for row in self.payables + self.receivables:
			if not (row.reference_document_type and row.reference_document):
				continue

			meta = frappe.get_meta(row.reference_document_type)
			fields = [field for field in ("employee", "company") if meta.has_field(field)]
			reference = frappe.db.get_value(
				row.reference_document_type,
				row.reference_document,
				["docstatus", *fields],
				as_dict=True,
			)
			if (
				not reference
				or (meta.is_submittable and reference.docstatus != 1)
				or ("employee" in fields and reference.employee != self.employee)
				or ("company" in fields and reference.company != self.company)
			):
				frappe.throw(
					_("Row {0}: {1} {2} must be a submitted document of Employee {3} and Company {4}").format(
						row.idx,
						row.reference_document_type,
						frappe.bold(row.reference_document),
						frappe.bold(self.employee),
						frappe.bold(self.company),
					),
					title=_("Invalid Reference Document"),
				)

			if row.parentfield == "payables":
				self.validate_payable_reference(row)

			if row.reference_document_type in OUTSTANDING_REFERENCE_DOCTYPES:
				outstanding = flt(
					get_reference_account_and_amount(row.reference_document_type, row.reference_document)[1]
				)
				if flt(row.amount, row.precision("amount")) > flt(outstanding, row.precision("amount")):
					frappe.throw(
						_(
							"Row {0}: Amount {1} cannot be greater than the outstanding amount {2} of {3} {4}"
						).format(
							row.idx,
							row.amount,
							outstanding,
							row.reference_document_type,
							frappe.bold(row.reference_document),
						),
						title=_("Invalid Amount"),
					)

	def validate_payable_reference(self, row):
		if row.reference_document_type == "Gratuity" and frappe.db.get_value(
			"Gratuity", row.reference_document, "pay_via_salary_slip"
		):
			frappe.throw(
				_("Row {0}: Gratuity {1} is paid via Salary Slip and cannot be settled here").format(
					row.idx, frappe.bold(row.reference_document)
				)
			)

		if row.reference_document_type == "Leave Encashment" and not frappe.db.get_value(
			"Leave Encashment", row.reference_document, "pay_via_payment_entry"
		):
			frappe.throw(
				_("Row {0}: Leave Encashment {1} is paid via Salary Slip and cannot be settled here").format(
					row.idx, frappe.bold(row.reference_document)
				)
			)

	def validate_settlement(self, component_type):
		for data in self.get(component_type, []):
			if data.status == "Unsettled":
				frappe.throw(
					_("Settle all Payables and Receivables before submission"),
					title=_("Unsettled Transactions"),
				)

	def validate_assets(self):
		pending_returns = []

		for data in self.assets_allocated:
			if data.action == "Return":
				if data.status == "Owned":
					pending_returns.append(_("Row {0}: {1}").format(data.idx, frappe.bold(data.asset_name)))
			elif data.action == "Recover Cost":
				data.status = "Owned"

		if pending_returns:
			msg = _("All allocated assets should be returned before submission")
			msg += "<br><br>"
			msg += ", ".join(d for d in pending_returns)
			frappe.throw(msg, title=_("Pending Asset Returns"))

	@frappe.whitelist()
	def get_outstanding_statements(self):
		if not self.relieving_date:
			frappe.throw(
				_("Set Relieving Date for Employee: {0}").format(get_link_to_form("Employee", self.employee))
			)

		if not self.payables:
			self.add_withheld_salary_slips()
			components = self.get_payable_component()
			self.create_component_row(components, "payables")
		self.add_outstanding_employee_advances()
		self.create_component_row(self.get_receivable_component(), "receivables")
		self.get_assets_statements()

	def get_assets_statements(self):
		if not len(self.get("assets_allocated", [])):
			for data in self.get_assets_movement():
				self.append("assets_allocated", data)

	def set_total_asset_recovery_cost(self):
		total_cost = 0
		for data in self.assets_allocated:
			if data.action == "Recover Cost":
				if not data.description:
					data.description = _("Asset Recovery Cost for {0}: {1}").format(
						data.reference, data.asset_name
					)
				total_cost += flt(data.cost)

		self.total_asset_recovery_cost = flt(total_cost, self.precision("total_asset_recovery_cost"))

	def set_totals(self):
		total_payable = sum(flt(row.amount) for row in self.payables)
		total_receivable = sum(flt(row.amount) for row in self.receivables)

		self.total_payable_amount = flt(total_payable, self.precision("total_payable_amount"))
		self.total_receivable_amount = flt(
			total_receivable + flt(self.total_asset_recovery_cost),
			self.precision("total_receivable_amount"),
		)

	def add_withheld_salary_slips(self):
		salary_slips = frappe.get_all(
			"Salary Slip",
			filters={
				"employee": self.employee,
				"status": "Withheld",
				"docstatus": 1,
			},
			fields=["name", "net_pay"],
		)

		for slip in salary_slips:
			self.append(
				"payables",
				{
					"status": "Unsettled",
					"component": "Salary Slip",
					"reference_document_type": "Salary Slip",
					"reference_document": slip.name,
					"amount": slip.net_pay,
					"paid_via_salary_slip": 1,
				},
			)

	def add_outstanding_employee_advances(self):
		"""
		Reconciles receivables with the employee's outstanding advances: placeholder rows and other
		employees' advances are dropped, rows not marked Settled are refreshed to the current balance,
		and missing advances are added.
		"""
		advances = frappe.get_all(
			"Employee Advance",
			filters={"employee": self.employee, "docstatus": 1},
			fields=["name", "advance_account", "paid_amount", "claimed_amount", "return_amount"],
		)
		outstanding_advances = {}
		for advance in advances:
			advance.outstanding = (
				flt(advance.paid_amount) - flt(advance.claimed_amount) - flt(advance.return_amount)
			)
			if advance.outstanding > 0:
				outstanding_advances[advance.name] = advance

		self.receivables = [
			row
			for row in self.receivables
			if row.component != "Employee Advance"
			or (row.reference_document in outstanding_advances)
			or (not row.reference_document and not outstanding_advances)
		]

		referenced_advances = set()
		for row in self.receivables:
			advance = outstanding_advances.get(row.reference_document)
			if not advance:
				continue

			referenced_advances.add(advance.name)
			if row.status != "Settled":
				row.account = advance.advance_account
				row.amount = advance.outstanding

		for advance in outstanding_advances.values():
			if advance.name in referenced_advances:
				continue

			self.append(
				"receivables",
				{
					"status": "Unsettled",
					"component": "Employee Advance",
					"reference_document_type": "Employee Advance",
					"reference_document": advance.name,
					"account": advance.advance_account,
					"amount": advance.outstanding,
				},
			)

	def create_component_row(self, components, component_type):
		existing_components = {row.component for row in self.get(component_type)}

		for component in components:
			if component in existing_components:
				continue

			self.append(
				component_type,
				{
					"status": "Unsettled",
					"reference_document_type": component if component != "Bonus" else "Additional Salary",
					"component": component,
				},
			)

	def get_payable_component(self):
		return [
			"Gratuity",
			"Expense Claim",
			"Bonus",
			"Leave Encashment",
		]

	def get_receivable_component(self):
		receivables = ["Employee Advance"]
		if "lending" in frappe.get_installed_apps():
			receivables.append("Loan")
		return receivables

	def get_assets_movement(self):
		asset_movements = frappe.get_all(
			"Asset Movement Item",
			filters={"docstatus": 1},
			fields=["asset", "from_employee", "to_employee", "parent", "asset_name"],
			or_filters={"from_employee": self.employee, "to_employee": self.employee},
		)

		data = []
		latest_inward_movement = {}
		movement_balance = {}
		for movement in asset_movements:
			if movement.to_employee and movement.to_employee == self.employee:
				movement.date = frappe.db.get_value("Asset Movement", movement.parent, "transaction_date")
				movement_balance[movement.asset] = movement_balance.get(movement.asset, 0) + 1
				latest = latest_inward_movement.get(movement.asset)
				if not latest or movement.date > latest.date:
					latest_inward_movement[movement.asset] = movement

			if movement.from_employee and movement.from_employee == self.employee:
				movement_balance[movement.asset] = movement_balance.get(movement.asset, 0) - 1

		for asset, movement in latest_inward_movement.items():
			if movement_balance[asset] > 0:
				cost = frappe.db.get_value("Asset", asset, "total_asset_cost")
				data.append(
					{
						"reference": movement.parent,
						"asset_name": movement.asset_name,
						"date": movement.date,
						"actual_cost": cost,
						"cost": cost,
						"action": "Return",
						"status": "Owned",
					}
				)
		return data

	@frappe.whitelist()
	def create_journal_entry(self):
		precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")
		jv = frappe.new_doc("Journal Entry")
		jv.company = self.company
		jv.voucher_type = "Bank Entry"
		jv.posting_date = today()

		payable_via_journal = sum(flt(row.amount) for row in self.payables if not row.paid_via_salary_slip)
		difference = flt(payable_via_journal, self.precision("total_payable_amount")) - flt(
			self.total_receivable_amount
		)

		for data in self.payables:
			if flt(data.amount) > 0 and not data.paid_via_salary_slip:
				account_dict = {
					"account": data.account,
					"debit_in_account_currency": flt(data.amount, precision),
					"user_remark": data.remark,
				}
				if data.reference_document_type in ["Expense Claim", "Gratuity", "Leave Encashment"]:
					account_dict["party_type"] = "Employee"
					account_dict["party"] = self.employee
				if data.reference_document_type == "Expense Claim":
					account_dict["reference_type"] = "Expense Claim"
					account_dict["reference_name"] = data.reference_document

				jv.append("accounts", account_dict)

		for data in self.receivables:
			if flt(data.amount) > 0:
				account_dict = {
					"account": data.account,
					"credit_in_account_currency": flt(data.amount, precision),
					"user_remark": data.remark,
				}
				if data.reference_document_type == "Employee Advance":
					account_dict.update(
						{
							"party_type": "Employee",
							"party": self.employee,
							"reference_type": "Employee Advance",
							"reference_name": data.reference_document,
							"is_advance": "Yes",
						}
					)

				jv.append("accounts", account_dict)

		for data in self.assets_allocated:
			if data.action == "Recover Cost":
				jv.append(
					"accounts",
					{
						"account": data.account,
						"credit_in_account_currency": flt(data.cost, precision),
						"party_type": "Employee",
						"party": self.employee,
						"user_remark": data.description,
					},
				)

		jv.append(
			"accounts",
			{
				"credit_in_account_currency": difference if difference > 0 else 0,
				"debit_in_account_currency": -(difference) if difference < 0 else 0,
				"reference_type": self.doctype,
				"reference_name": self.name,
			},
		)
		return jv

	def update_linked_payable_documents(self):
		"""update payment status in linked payable documents"""
		for payable in self.payables:
			if (
				payable.reference_document_type in ["Gratuity", "Leave Encashment"]
				and payable.reference_document
			):
				frappe.get_doc(
					payable.reference_document_type, payable.reference_document
				).set_total_advance_paid()


@frappe.whitelist()
def get_account_and_amount(ref_doctype: str, ref_document: str, company: str) -> list | None:
	if not ref_doctype or not ref_document:
		return None

	frappe.has_permission(ref_doctype, "read", ref_document, throw=True)
	return get_reference_account_and_amount(ref_doctype, ref_document, company)


def get_reference_account_and_amount(ref_doctype: str, ref_document: str, company: str | None = None):
	if ref_doctype == "Salary Slip":
		salary_details = frappe.db.get_value(
			"Salary Slip", ref_document, ["payroll_entry", "net_pay"], as_dict=1
		)
		amount = salary_details.net_pay
		payable_account = (
			frappe.db.get_value("Payroll Entry", salary_details.payroll_entry, "payroll_payable_account")
			if salary_details.payroll_entry
			else None
		)
		return [payable_account, amount]

	if ref_doctype == "Gratuity":
		payable_account, amount, paid_amount = frappe.db.get_value(
			"Gratuity", ref_document, ["payable_account", "amount", "paid_amount"]
		)
		return [payable_account, flt(amount) - flt(paid_amount)]

	if ref_doctype == "Expense Claim":
		payable_account = frappe.db.get_value("Expense Claim", ref_document, "payable_account")
		return [payable_account, get_outstanding_amount_for_claim(ref_document)]

	if ref_doctype == "Loan":
		details = frappe.db.get_value(
			"Loan", ref_document, ["payment_account", "total_payment", "total_amount_paid"], as_dict=1
		)
		payment_account = details.payment_account
		amount = details.total_payment - details.total_amount_paid
		return [payment_account, amount]

	if ref_doctype == "Employee Advance":
		details = frappe.db.get_value(
			"Employee Advance",
			ref_document,
			["advance_account", "paid_amount", "claimed_amount", "return_amount"],
			as_dict=1,
		)
		payment_account = details.advance_account
		amount = details.paid_amount - (details.claimed_amount + details.return_amount)
		return [payment_account, amount]

	if ref_doctype == "Leave Encashment":
		payable_account, amount, paid_amount = frappe.db.get_value(
			"Leave Encashment", ref_document, ["payable_account", "encashment_amount", "paid_amount"]
		)
		return [payable_account, flt(amount) - flt(paid_amount)]


def get_amount_paid_via_full_and_final_statement(reference_doctype: str, reference_name: str) -> float:
	fnf = frappe.qb.DocType("Full and Final Statement")
	payable = frappe.qb.DocType("Full and Final Outstanding Statement")
	amount = (
		frappe.qb.from_(payable)
		.join(fnf)
		.on(fnf.name == payable.parent)
		.select(Sum(payable.amount))
		.where(
			(payable.parenttype == "Full and Final Statement")
			& (payable.parentfield == "payables")
			& (payable.reference_document_type == reference_doctype)
			& (payable.reference_document == reference_name)
			& (payable.paid_via_salary_slip == 0)
			& (fnf.docstatus == 1)
			& (fnf.status == "Paid")
		)
	).run()[0][0]
	return flt(amount)


def update_full_and_final_statement_status(doc, method=None):
	"""Updates FnF status on Journal Entry Submission/Cancellation"""
	status = "Paid" if doc.docstatus == 1 else "Unpaid"

	for entry in doc.accounts:
		if entry.reference_type == "Full and Final Statement":
			fnf = frappe.get_doc("Full and Final Statement", entry.reference_name)
			fnf.db_set("status", status)
			fnf.notify_update()
			fnf.update_linked_payable_documents()
