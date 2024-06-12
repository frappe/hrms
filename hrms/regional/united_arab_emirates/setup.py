# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe


def setup():
	create_gratuity_rules_for_uae()


def create_gratuity_rules_for_uae():
	docs = get_gratuity_rules()
	for d in docs:
		doc = frappe.get_doc(d)
		doc.insert(ignore_if_duplicate=True, ignore_permissions=True, ignore_mandatory=True)


def get_gratuity_rules():
	return [
		{
			"doctype": "Gratuity Rule",
			"name": "Rule Under Limited Contract (UAE)",
			"calculate_gratuity_amount_based_on": "Sum of all previous slabs",
			"work_experience_calculation_method": "Take Exact Completed Years",
			"minimum_year_for_gratuity": 1,
			"gratuity_rule_slabs": [
				{"from_year": 0, "to_year": 1, "fraction_of_applicable_earnings": 0},
				{"from_year": 1, "to_year": 5, "fraction_of_applicable_earnings": 21 / 30},
				{"from_year": 5, "to_year": 0, "fraction_of_applicable_earnings": 1},
			],
		},
		{
			"doctype": "Gratuity Rule",
			"name": "Rule Under Unlimited Contract on termination (UAE)",
			"calculate_gratuity_amount_based_on": "Current Slab",
			"work_experience_calculation_method": "Take Exact Completed Years",
			"minimum_year_for_gratuity": 1,
			"gratuity_rule_slabs": [
				{"from_year": 0, "to_year": 1, "fraction_of_applicable_earnings": 0},
				{"from_year": 1, "to_year": 5, "fraction_of_applicable_earnings": 21 / 30},
				{"from_year": 5, "to_year": 0, "fraction_of_applicable_earnings": 1},
			],
		},
		{
			"doctype": "Gratuity Rule",
			"name": "Rule Under Unlimited Contract on resignation (UAE)",
			"calculate_gratuity_amount_based_on": "Current Slab",
			"work_experience_calculation_method": "Take Exact Completed Years",
			"minimum_year_for_gratuity": 1,
			"gratuity_rule_slabs": [
				{"from_year": 0, "to_year": 1, "fraction_of_applicable_earnings": 0},
				{"from_year": 1, "to_year": 3, "fraction_of_applicable_earnings": 1 / 3 * 21 / 30},
				{"from_year": 3, "to_year": 5, "fraction_of_applicable_earnings": 2 / 3 * 21 / 30},
				{"from_year": 5, "to_year": 0, "fraction_of_applicable_earnings": 21 / 30},
			],
		},
	]
