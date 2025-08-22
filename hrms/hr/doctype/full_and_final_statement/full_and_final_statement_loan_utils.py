# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from typing import TYPE_CHECKING

import frappe
from frappe import _

from hrms.payroll.doctype.salary_slip.salary_slip_loan_utils import if_lending_app_installed

if TYPE_CHECKING:
	from hrms.hr.doctype.full_and_final_statement.full_and_final_statement import FullandFinalStatement


@if_lending_app_installed
def process_loan_accrual(doc: "FullandFinalStatement"):
	from lending.loan_management.doctype.loan_interest_accrual.loan_interest_accrual import (
		make_loan_interest_accrual_entry,
	)
	from lending.loan_management.doctype.loan_repayment.loan_repayment import (
		calculate_amounts,
		create_repayment_entry,
		get_pending_principal_amount,
	)

	loan_receivables = []
	for receivable in doc.receivables:
		if receivable.component != "Loan":
			continue

		loan_receivables.append(receivable.reference_document)

	for loan in loan_receivables:
		loan_doc = frappe.get_doc("Loan", loan)
		loan_repayment_schedule = frappe.get_doc("Loan Repayment Schedule", {"loan": loan, "docstatus": 1})
		if loan_repayment_schedule.repayment_schedule:
			amounts = []
			for repayment_schedule in loan_repayment_schedule.repayment_schedule:
				amounts = calculate_amounts(loan, doc.transaction_date, "Normal Repayment")
				pending_principal_amount = get_pending_principal_amount(loan_doc)
				if not repayment_schedule.is_accrued:
					args = frappe._dict(
						{
							"loan": loan,
							"applicant_type": loan_doc.applicant_type,
							"applicant": loan_doc.applicant,
							"interest_income_account": loan_doc.interest_income_account,
							"loan_account": loan_doc.loan_account,
							"pending_principal_amount": amounts["pending_principal_amount"],
							"payable_principal": repayment_schedule.principal_amount,
							"interest_amount": repayment_schedule.interest_amount,
							"total_pending_interest_amount": pending_principal_amount,
							"penalty_amount": amounts["penalty_amount"],
							"posting_date": doc.transaction_date,
							"repayment_schedule_name": repayment_schedule.name,
							"accrual_type": "Regular",
							"due_date": doc.transaction_date,
						}
					)
					make_loan_interest_accrual_entry(args)
					frappe.db.set_value("Repayment Schedule", repayment_schedule.name, "is_accrued", 1)

			repayment_entry = create_repayment_entry(
				loan,
				doc.employee,
				doc.company,
				doc.transaction_date,
				loan_doc.loan_product,
				"Normal Repayment",
				amounts["interest_amount"],
				amounts["pending_principal_amount"],
				receivable.amount,
			)

			repayment_entry.save()
			repayment_entry.submit()


@if_lending_app_installed
def cancel_loan_repayment(doc: "FullandFinalStatement"):
	loan_receivables = []
	for receivable in doc.receivables:
		if receivable.component != "Loan":
			continue

		loan_receivables.append(receivable.reference_document)

	for loan in loan_receivables:
		posting_date = frappe.utils.getdate(doc.transaction_date)
		loan_repayment = frappe.get_doc(
			"Loan Repayment", {"against_loan": loan, "docstatus": 1, "posting_date": posting_date}
		)

		if loan_repayment:
			loan_repayment.cancel()

		loan_interest_accruals = frappe.get_all(
			"Loan Interest Accrual", filters={"loan": loan, "docstatus": 1, "posting_date": posting_date}
		)
		for accrual in loan_interest_accruals:
			frappe.get_doc("Loan Interest Accrual", accrual.name).cancel()
