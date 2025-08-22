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
		except Exception as e:
			frappe.log_error("Unable to delete country fixtures for Frappe HR")
			msg = _("Failed to delete defaults for country {0}.").format(frappe.bold(country))
			msg += "<br><br>" + _("{0}: {1}").format(frappe.bold(_("Error")), get_error_message(e))
			frappe.throw(msg, title=_("Country Fixture Deletion Failed"))


def run_regional_setup(country):
	try:
		module_name = f"hrms.regional.{frappe.scrub(country)}.setup.setup"
		frappe.get_attr(module_name)()
	except ImportError:
		pass
	except Exception as e:
		frappe.log_error("Unable to setup country fixtures for Frappe HR")
		msg = _("Failed to setup defaults for country {0}.").format(frappe.bold(country))
		msg += "<br><br>" + _("{0}: {1}").format(frappe.bold(_("Error")), get_error_message(e))
		frappe.throw(msg, title=_("Country Setup failed"))


def get_error_message(error) -> str:
	try:
		message_log = frappe.message_log.pop() if frappe.message_log else str(error)
		if isinstance(message_log, str):
			error_message = json.loads(message_log).get("message")
		else:
			error_message = message_log.get("message")
	except Exception:
		error_message = message_log

	return error_message


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
		with open(file_path) as f:
			return f.read()
	except OSError:
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
					"The currency of {0} should be same as the company's default currency. Please select another account."
				).format(frappe.bold(_("Default Payroll Payable Account")))
			)


def handle_linked_docs(doc, method=None):
	delete_docs_with_company_field(doc)
	clear_company_field_for_single_doctypes(doc)


def delete_docs_with_company_field(doc, method=None):
	"""
	Deletes records from linked doctypes where the 'company' field matches the company's name
	"""
	company_data_to_be_ignored = frappe.get_hooks("company_data_to_be_ignored") or []
	for doctype in company_data_to_be_ignored:
		records_to_delete = frappe.get_all(doctype, filters={"company": doc.name}, pluck="name")
		if records_to_delete:
			frappe.db.delete(doctype, {"name": ["in", records_to_delete]})


def clear_company_field_for_single_doctypes(doc):
	"""
	Clears the 'company' value in Single doctypes where applicable
	"""
	single_docs = get_single_doctypes_with_company_field()
	singles = frappe.qb.DocType("Singles")
	(
		frappe.qb.update(singles)
		.set(singles.value, "")
		.where(singles.doctype.isin(single_docs))
		.where(singles.field == "company")
		.where(singles.value == doc.name)
	).run()


def get_single_doctypes_with_company_field():
	DocType = frappe.qb.DocType("DocType")
	DocField = frappe.qb.DocType("DocField")

	return (
		frappe.qb.from_(DocField)
		.select(DocField.parent)
		.where(
			(DocField.fieldtype == "Link")
			& (DocField.options == "Company")
			& (
				DocField.parent.isin(
					frappe.qb.from_(DocType)
					.select(DocType.name)
					.where((DocType.issingle == 1) & (DocType.module.isin(["HR", "Payroll"])))
				)
			)
		)
	).run(pluck=True)
