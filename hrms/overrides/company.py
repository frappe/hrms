# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import json

import frappe
from frappe import _

from erpnext.accounts.doctype.account.account import get_account_currency


def make_company_fixtures(doc, method=None):
	if not frappe.flags.country_change:
		return

	run_regional_setup(doc.country)
	make_salary_components(doc.country)


def delete_company_fixtures():
	countries = frappe.get_all(
		"Company",
		distinct="True",
		pluck="country",
	)

	for country in countries:
		try:
			module_name = f"hrms.regional.{frappe.scrub(country)}.setup.uninstall"
			frappe.get_attr(module_name)()
		except (ImportError, AttributeError):
			# regional file or method does not exist
			pass
		except Exception:
			frappe.log_error("Unable to delete country fixtures for HRMS")
			frappe.throw(
				_("Failed to delete defaults for country {0}. Please contact support.").format(
					frappe.bold(country)
				)
			)


def run_regional_setup(country):
	try:
		module_name = f"hrms.regional.{frappe.scrub(country)}.setup.setup"
		frappe.get_attr(module_name)()
	except ImportError:
		pass
	except Exception:
		frappe.log_error("Unable to setup country fixtures for HRMS")
		frappe.throw(
			_("Failed to setup defaults for country {0}. Please contact support.").format(
				frappe.bold(country)
			)
		)


def make_salary_components(country):
	docs = []

	file_name = "salary_components.json"

	# default components already added
	if not frappe.db.exists("Salary Component", "Basic"):
		file_path = frappe.get_app_path("hrms", "payroll", "data", file_name)
		docs.extend(json.loads(read_data_file(file_path)))

	file_path = frappe.get_app_path("hrms", "regional", frappe.scrub(country), "data", file_name)
	docs.extend(json.loads(read_data_file(file_path)))

	for d in docs:
		try:
			doc = frappe.get_doc(d)
			doc.flags.ignore_permissions = True
			doc.flags.ignore_mandatory = True
			doc.insert(ignore_if_duplicate=True)
		except frappe.NameError:
			frappe.clear_messages()
		except frappe.DuplicateEntryError:
			frappe.clear_messages()


def read_data_file(file_path):
	try:
		with open(file_path, "r") as f:
			return f.read()
	except IOError:
		return "{}"


def set_default_hr_accounts(doc, method=None):
	if frappe.local.flags.ignore_chart_of_accounts:
		return

	if not doc.default_payroll_payable_account:
		payroll_payable_account = frappe.db.get_value(
			"Account", {"account_name": _("Payroll Payable"), "company": doc.name, "is_group": 0}
		)

		doc.db_set("default_payroll_payable_account", payroll_payable_account)

	if not doc.default_employee_advance_account:
		employe_advance_account = frappe.db.get_value(
			"Account", {"account_name": _("Employee Advances"), "company": doc.name, "is_group": 0}
		)

		doc.db_set("default_employee_advance_account", employe_advance_account)


def validate_default_accounts(doc, method=None):
	if doc.default_payroll_payable_account:
		for_company = frappe.db.get_value("Account", doc.default_payroll_payable_account, "company")
		if for_company != doc.name:
			frappe.throw(
				_("Account {0} does not belong to company: {1}").format(
					doc.default_payroll_payable_account, doc.name
				)
			)

		if get_account_currency(doc.default_payroll_payable_account) != doc.default_currency:
			frappe.throw(
				_(
					"{0} currency must be same as company's default currency. Please select another account."
				).format(frappe.bold("Default Payroll Payable Account"))
			)
