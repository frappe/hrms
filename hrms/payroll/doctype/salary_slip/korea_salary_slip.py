# Copyright (c) 2026, contributors
# For license information, please see license.txt

import frappe


def apply_korea_salary_slip_fields(doc, method=None):
    if not _is_south_korea_company(getattr(doc, "company", None)):
        return

    employee_flags = _get_employee_korea_flags(getattr(doc, "employee", None))
    is_foreign_flat_tax = bool(getattr(employee_flags, "kr_foreign_flat_tax", 0))

    doc.kr_tax_method = "19% flat" if is_foreign_flat_tax else "간이세액표"
    doc.kr_taxable_pay = _coerce_amount(getattr(doc, "gross_pay", 0)) - _coerce_amount(
        getattr(doc, "non_taxable_earnings", 0)
    )
    doc.kr_nontaxable_pay = _coerce_amount(getattr(doc, "non_taxable_earnings", 0))
    doc.kr_income_tax = _coerce_amount(getattr(doc, "current_month_income_tax", 0))
    doc.kr_total_deductions = _coerce_amount(getattr(doc, "total_deduction", 0))


def _is_south_korea_company(company):
    if not company:
        return False

    return frappe.db.get_value("Company", company, "country") == "South Korea"


def _get_employee_korea_flags(employee):
    if not employee:
        return frappe._dict() if hasattr(frappe, "_dict") else type("Flags", (), {})()

    result = frappe.db.get_value(
        "Employee",
        employee,
        ["kr_foreign_flat_tax", "kr_withholding_rate"],
        as_dict=True,
        cache=True,
    )
    if result:
        return result
    return frappe._dict() if hasattr(frappe, "_dict") else type("Flags", (), {})()


def _coerce_amount(value):
    if value in (None, ""):
        return 0
    return float(value)
