# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields


def setup():
	make_custom_fields()
	add_custom_roles_for_reports()
	create_gratuity_rule_for_india()


def uninstall():
	custom_fields = get_custom_fields()
	delete_custom_fields(custom_fields)


def make_custom_fields(update=True):
	custom_fields = get_custom_fields()
	create_custom_fields(custom_fields, update=update)


def get_custom_fields():
	return {
		"Salary Component": [
			{
				"fieldname": "component_type",
				"label": "Component Type",
				"fieldtype": "Select",
				"insert_after": "description",
				"options": (
					"\nProvident Fund\nAdditional Provident Fund\nProvident Fund Loan\nProfessional Tax"
				),
				"depends_on": 'eval:doc.type == "Deduction"',
				"translatable": 0,
			},
		],
		"Employee": [
			{
				"fieldname": "bank_cb",
				"fieldtype": "Column Break",
				"insert_after": "bank_ac_no",
			},
			{
				"fieldname": "ifsc_code",
				"label": "IFSC Code",
				"fieldtype": "Data",
				"insert_after": "bank_cb",
				"print_hide": 1,
				"depends_on": 'eval:doc.salary_mode == "Bank"',
				"translatable": 0,
			},
			{
				"fieldname": "pan_number",
				"label": "PAN Number",
				"fieldtype": "Data",
				"insert_after": "payroll_cost_center",
				"print_hide": 1,
				"translatable": 0,
			},
			{
				"fieldname": "micr_code",
				"label": "MICR Code",
				"fieldtype": "Data",
				"insert_after": "ifsc_code",
				"print_hide": 1,
				"depends_on": 'eval:doc.salary_mode == "Bank"',
				"translatable": 0,
			},
			{
				"fieldname": "provident_fund_account",
				"label": "Provident Fund Account",
				"fieldtype": "Data",
				"insert_after": "pan_number",
				"translatable": 0,
			},
		],
		"Company": [
			{
				"fieldname": "hra_section",
				"label": "HRA Settings",
				"fieldtype": "Section Break",
				"insert_after": "asset_received_but_not_billed",
				"collapsible": 1,
			},
			{
				"fieldname": "basic_component",
				"label": "Basic Component",
				"fieldtype": "Link",
				"options": "Salary Component",
				"insert_after": "hra_section",
			},
			{
				"fieldname": "hra_component",
				"label": "HRA Component",
				"fieldtype": "Link",
				"options": "Salary Component",
				"insert_after": "basic_component",
			},
			{
				"fieldname": "hra_column_break",
				"fieldtype": "Column Break",
				"insert_after": "hra_component",
			},
			{
				"fieldname": "arrear_component",
				"label": "Arrear Component",
				"fieldtype": "Link",
				"options": "Salary Component",
				"insert_after": "hra_column_break",
			},
		],
		"Employee Tax Exemption Declaration": [
			{
				"fieldname": "hra_section",
				"label": "HRA Exemption",
				"fieldtype": "Section Break",
				"insert_after": "declarations",
			},
			{
				"fieldname": "monthly_house_rent",
				"label": "Monthly House Rent",
				"fieldtype": "Currency",
				"insert_after": "hra_section",
			},
			{
				"fieldname": "rented_in_metro_city",
				"label": "Rented in Metro City",
				"fieldtype": "Check",
				"insert_after": "monthly_house_rent",
				"depends_on": "monthly_house_rent",
			},
			{
				"fieldname": "salary_structure_hra",
				"label": "HRA as per Salary Structure",
				"fieldtype": "Currency",
				"insert_after": "rented_in_metro_city",
				"read_only": 1,
				"depends_on": "monthly_house_rent",
			},
			{
				"fieldname": "hra_column_break",
				"fieldtype": "Column Break",
				"insert_after": "salary_structure_hra",
				"depends_on": "monthly_house_rent",
			},
			{
				"fieldname": "annual_hra_exemption",
				"label": "Annual HRA Exemption",
				"fieldtype": "Currency",
				"insert_after": "hra_column_break",
				"read_only": 1,
				"depends_on": "monthly_house_rent",
			},
			{
				"fieldname": "monthly_hra_exemption",
				"label": "Monthly HRA Exemption",
				"fieldtype": "Currency",
				"insert_after": "annual_hra_exemption",
				"read_only": 1,
				"depends_on": "monthly_house_rent",
			},
		],
		"Employee Tax Exemption Proof Submission": [
			{
				"fieldname": "hra_section",
				"label": "HRA Exemption",
				"fieldtype": "Section Break",
				"insert_after": "tax_exemption_proofs",
			},
			{
				"fieldname": "house_rent_payment_amount",
				"label": "House Rent Payment Amount",
				"fieldtype": "Currency",
				"insert_after": "hra_section",
			},
			{
				"fieldname": "rented_in_metro_city",
				"label": "Rented in Metro City",
				"fieldtype": "Check",
				"insert_after": "house_rent_payment_amount",
				"depends_on": "house_rent_payment_amount",
			},
			{
				"fieldname": "rented_from_date",
				"label": "Rented From Date",
				"fieldtype": "Date",
				"insert_after": "rented_in_metro_city",
				"depends_on": "house_rent_payment_amount",
			},
			{
				"fieldname": "rented_to_date",
				"label": "Rented To Date",
				"fieldtype": "Date",
				"insert_after": "rented_from_date",
				"depends_on": "house_rent_payment_amount",
			},
			{
				"fieldname": "hra_column_break",
				"fieldtype": "Column Break",
				"insert_after": "rented_to_date",
				"depends_on": "house_rent_payment_amount",
			},
			{
				"fieldname": "monthly_house_rent",
				"label": "Monthly House Rent",
				"fieldtype": "Currency",
				"insert_after": "hra_column_break",
				"read_only": 1,
				"depends_on": "house_rent_payment_amount",
			},
			{
				"fieldname": "monthly_hra_exemption",
				"label": "Monthly Eligible Amount",
				"fieldtype": "Currency",
				"insert_after": "monthly_house_rent",
				"read_only": 1,
				"depends_on": "house_rent_payment_amount",
			},
			{
				"fieldname": "total_eligible_hra_exemption",
				"label": "Total Eligible HRA Exemption",
				"fieldtype": "Currency",
				"insert_after": "monthly_hra_exemption",
				"read_only": 1,
				"depends_on": "house_rent_payment_amount",
			},
		],
	}


def add_custom_roles_for_reports():
	for report_name in (
		"Professional Tax Deductions",
		"Provident Fund Deductions",
		"Income Tax Deductions",
	):
		if not frappe.db.get_value("Custom Role", dict(report=report_name)):
			frappe.get_doc(
				dict(
					doctype="Custom Role",
					report=report_name,
					roles=[dict(role="HR User"), dict(role="HR Manager"), dict(role="Employee")],
				)
			).insert()


def create_gratuity_rule_for_india():
	if not frappe.db.exists("DocType", "Gratuity Rule"):
		return

	if frappe.db.exists("Gratuity Rule", "Indian Standard Gratuity Rule"):
		return

	rule = frappe.new_doc("Gratuity Rule")
	rule.update(
		{
			"name": "Indian Standard Gratuity Rule",
			"calculate_gratuity_amount_based_on": "Current Slab",
			"work_experience_calculation_method": "Round Off Work Experience",
			"minimum_year_for_gratuity": 5,
			"gratuity_rule_slabs": [
				{
					"from_year": 0,
					"to_year": 0,
					"fraction_of_applicable_earnings": 15 / 26,
				}
			],
		}
	)
	rule.flags.ignore_mandatory = True
	rule.save()
