# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import date

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, get_first_day, get_last_day, getdate

import erpnext

from hrms.hr.utils import calculate_tax_with_marginal_relief


class IncomeTaxSlab(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.payroll.doctype.income_tax_slab_other_charges.income_tax_slab_other_charges import (
			IncomeTaxSlabOtherCharges,
		)
		from hrms.payroll.doctype.taxable_salary_slab.taxable_salary_slab import TaxableSalarySlab

		allow_tax_exemption: DF.Check
		amended_from: DF.Link | None
		company: DF.Link | None
		currency: DF.Link
		disabled: DF.Check
		effective_from: DF.Date
		other_taxes_and_charges: DF.Table[IncomeTaxSlabOtherCharges]
		slabs: DF.Table[TaxableSalarySlab]
		standard_tax_exemption_amount: DF.Currency
		tax_relief_limit: DF.Currency
	# end: auto-generated types

	def validate(self):
		if self.company:
			self.currency = erpnext.get_company_currency(self.company)


def calculate_tax_by_tax_slab(annual_taxable_earning, tax_slab, eval_globals=None, eval_locals=None):
	eval_globals = eval_globals or {}
	eval_locals = eval_locals or {}

	if annual_taxable_earning <= tax_slab.tax_relief_limit:
		return 0, 0

	tax_amount = calculate_base_tax_from_tax_slabs(
		annual_taxable_earning, tax_slab, eval_globals, eval_locals
	)

	if tax_with_marginal_relief := calculate_tax_with_marginal_relief(
		tax_slab, tax_amount, annual_taxable_earning
	):
		tax_amount = tax_with_marginal_relief

	tax_amount, surcharge = apply_surcharge_with_marginal_relief(
		tax_amount, annual_taxable_earning, tax_slab, eval_globals, eval_locals
	)

	tax_amount, other_taxes = calculate_other_charges(tax_amount, annual_taxable_earning, tax_slab)
	return tax_amount, surcharge + other_taxes


def calculate_base_tax_from_tax_slabs(annual_taxable_earning, tax_slab, eval_globals, eval_locals):
	tax_amount = 0
	eval_locals.update({"annual_taxable_earning": annual_taxable_earning})

	for slab in tax_slab.slabs:
		cond = cstr(slab.condition).strip()
		if cond and not eval_tax_slab_condition(cond, eval_globals, eval_locals):
			continue
		if not slab.to_amount and annual_taxable_earning >= slab.from_amount:
			tax_amount += (annual_taxable_earning - slab.from_amount + 1) * slab.percent_deduction * 0.01
			continue
		if annual_taxable_earning >= slab.from_amount and annual_taxable_earning < slab.to_amount:
			tax_amount += (annual_taxable_earning - slab.from_amount + 1) * slab.percent_deduction * 0.01
		elif annual_taxable_earning >= slab.from_amount and annual_taxable_earning >= slab.to_amount:
			tax_amount += (slab.to_amount - slab.from_amount + 1) * slab.percent_deduction * 0.01
	return tax_amount


def calculate_other_charges(tax_amount, annual_taxable_earning, tax_slab):
	total_other_taxes_and_charges = 0
	for d in tax_slab.other_taxes_and_charges:
		if flt(d.min_taxable_income) and flt(d.min_taxable_income) > annual_taxable_earning:
			continue

		if flt(d.max_taxable_income) and flt(d.max_taxable_income) < annual_taxable_earning:
			continue
		other_taxes_and_charges = tax_amount * flt(d.percent) / 100
		tax_amount += other_taxes_and_charges
		total_other_taxes_and_charges += other_taxes_and_charges

	return tax_amount, total_other_taxes_and_charges


def eval_tax_slab_condition(condition, eval_globals=None, eval_locals=None):
	if not eval_globals:
		eval_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": date,
			"getdate": getdate,
			"get_first_day": get_first_day,
			"get_last_day": get_last_day,
		}
	try:
		condition = condition.strip()
		if condition:
			return frappe.safe_eval(condition, eval_globals, eval_locals)
	except NameError as err:
		frappe.throw(
			_("{0} <br> This error can be due to missing or deleted field.").format(str(err)),
			title=_("Name error"),
		)
	except SyntaxError as err:
		frappe.throw(_("Syntax error in condition: {0} in Income Tax Slab").format(str(err)))
	except Exception as e:
		frappe.throw(_("Error in formula or condition: {0} in Income Tax Slab").format(str(e)))
		raise


@erpnext.allow_regional
def apply_surcharge_with_marginal_relief(
	tax_amount, annual_taxable_earning, tax_slab, eval_globals, eval_locals
):
	return tax_amount, 0
