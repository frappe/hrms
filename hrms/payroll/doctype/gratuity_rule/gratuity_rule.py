# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class GratuityRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.payroll.doctype.gratuity_applicable_component.gratuity_applicable_component import (
			GratuityApplicableComponent,
		)
		from hrms.payroll.doctype.gratuity_rule_slab.gratuity_rule_slab import GratuityRuleSlab

		applicable_earnings_component: DF.TableMultiSelect[GratuityApplicableComponent]
		calculate_gratuity_amount_based_on: DF.Literal["Current Slab", "Sum of all previous slabs"]
		disable: DF.Check
		gratuity_rule_slabs: DF.Table[GratuityRuleSlab]
		minimum_year_for_gratuity: DF.Int
		total_working_days_per_year: DF.Float
		work_experience_calculation_function: DF.Literal[
			"Round off Work Experience", "Take Exact Completed Years", "Manual"
		]
	# end: auto-generated types

	def validate(self):
		for current_slab in self.gratuity_rule_slabs:
			if (current_slab.from_year > current_slab.to_year) and current_slab.to_year != 0:
				frappe.throw(
					_("Row {0}: From (Year) can not be greater than To (Year)").format(current_slab.idx)
				)

			if (
				current_slab.to_year == 0
				and current_slab.from_year == 0
				and len(self.gratuity_rule_slabs) > 1
			):
				frappe.throw(
					_("You can not define multiple slabs if you have a slab with no lower and upper limits.")
				)


def get_gratuity_rule(name, slabs, **args):
	args = frappe._dict(args)

	rule = frappe.new_doc("Gratuity Rule")
	rule.name = name
	rule.calculate_gratuity_amount_based_on = args.calculate_gratuity_amount_based_on or "Current Slab"
	rule.work_experience_calculation_method = (
		args.work_experience_calculation_method or "Take Exact Completed Years"
	)
	rule.minimum_year_for_gratuity = 1

	for slab in slabs:
		slab = frappe._dict(slab)
		rule.append("gratuity_rule_slabs", slab)
	return rule
