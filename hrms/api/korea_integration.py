from __future__ import annotations

import inspect
import json
import re
from contextlib import contextmanager
from copy import deepcopy
from datetime import date, datetime
from typing import Any

import frappe

DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500
LOCK_TTL_SECONDS = 10
BLOCKED_PII_FIELDS = {
    "resident_registration_number",
    "foreigner_registration_number",
    "bank_account_number",
    "address",
}
WORKSITE_FIELD_CANDIDATES = {
    "business_registration_number": ["custom_business_registration_number", "business_registration_number"],
    "worksite_code": ["custom_worksite_code", "worksite_code"],
    "status": ["custom_worksite_status", "status"],
    "effective_from": ["custom_effective_from", "effective_from"],
    "effective_to": ["custom_effective_to", "effective_to"],
    "source_modified": ["custom_source_modified", "source_modified"],
    "sync_status": ["custom_sync_status", "sync_status"],
    "last_sync_payload": ["custom_last_sync_payload", "last_sync_payload"],
}
EMPLOYMENT_TYPE_CATEGORY_MAP = {
    "정규직": "regular",
    "일용직": "daily",
    "파트타임": "part_time",
    "계약직": "contract",
}
WORKSITE_EVENT_TYPES = {"created", "updated", "deactivated"}
PAYROLL_REQUIRED_FIELDS = {
    "run_id",
    "employee_id",
    "pay_year_month",
    "taxable_items",
    "non_taxable_items",
    "social_insurance_deductions",
    "withholding_tax",
    "net_pay",
}
SOCIAL_INSURANCE_FIELDS = {
    "national_pension",
    "health_insurance",
    "long_term_care_insurance",
    "employment_insurance",
}
WITHHOLDING_TAX_FIELDS = {"income_tax", "local_income_tax"}
YEAR_END_SETTLEMENT_REQUIRED_FIELDS = {
    "run_id",
    "employee_id",
    "settlement_year",
    "settlement_kind",
    "applied_pay_year_month",
    "prepaid_tax",
    "determined_tax",
    "adjustment_tax",
}
SEVERANCE_REQUIRED_FIELDS = {
    "run_id",
    "employee_id",
    "retirement_date",
    "average_wage",
    "service_years",
    "severance_pay",
    "severance_income_tax",
    "net_pay",
}
SETTLEMENT_KINDS = {"annual_february", "mid_year_termination"}
PAY_YEAR_MONTH_PATTERN = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


@frappe.whitelist()
def export_employee_master(
    employee_id: str | None = None,
    company: str | None = None,
    branch: str | None = None,
    modified_after: str | None = None,
    include_inactive: bool = False,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict[str, Any]:
    page, page_size = _normalize_pagination(page, page_size)
    filters: dict[str, Any] = {}
    if employee_id:
        filters["name"] = employee_id
    if company:
        filters["company"] = company
    if branch:
        filters["branch"] = branch
    if modified_after:
        filters["modified"] = [">", modified_after]
    if not _coerce_bool(include_inactive):
        filters["status"] = "Active"

    fields = [
        "name",
        "employee_number",
        "employee_name",
        "company",
        "branch",
        "department",
        "designation",
        "employment_type",
        "date_of_joining",
        "relieving_date",
        "status",
        "modified",
    ]
    fields.extend(_get_optional_fields("Employee", ["visa_status_code"]))

    rows = frappe.get_all(
        "Employee",
        filters=filters,
        fields=fields,
        order_by="modified asc",
        start=(page - 1) * page_size,
        page_length=page_size + 1,
    )

    has_more = len(rows) > page_size
    payload = [_normalize_employee_row(row) for row in rows[:page_size]]
    return {"data": payload, "meta": _build_meta(page, page_size, has_more)}


@frappe.whitelist()
def export_time_and_leave(
    from_date: str,
    to_date: str,
    company: str | None = None,
    branch: str | None = None,
    employee_id: str | None = None,
    modified_after: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict[str, Any]:
    if not from_date or not to_date:
        frappe.throw("from_date and to_date are required")
    if _stringify_date(from_date) > _stringify_date(to_date):
        frappe.throw("from_date must be less than or equal to to_date")

    page, page_size = _normalize_pagination(page, page_size)
    query_page_length = _bounded_query_page_length(page_size)
    attendance_fields = ["name", "employee", "attendance_date", "status", "shift", "modified"]
    attendance_fields.extend(_get_optional_fields("Attendance"))

    attendance_filters: dict[str, Any] = {
        "attendance_date": ["between", [from_date, to_date]],
        "docstatus": 1,
    }
    leave_filters: dict[str, Any] = {
        "from_date": ["<=", to_date],
        "to_date": [">=", from_date],
        "docstatus": 1,
    }
    if employee_id:
        attendance_filters["employee"] = employee_id
        leave_filters["employee"] = employee_id
    if modified_after:
        attendance_filters["modified"] = [">", modified_after]
        leave_filters["modified"] = [">", modified_after]

    employee_filters = {k: v for k, v in {"company": company, "branch": branch}.items() if v}
    employee_whitelist = None
    if employee_filters:
        employee_whitelist = set(
            frappe.get_all("Employee", filters=employee_filters, pluck="name", page_length=query_page_length)
        )
        if not employee_whitelist:
            return {"data": [], "meta": _build_meta(page, page_size, False)}

    attendance_rows = frappe.get_all(
        "Attendance",
        filters=attendance_filters,
        fields=attendance_fields,
        order_by="employee asc, attendance_date asc",
        page_length=query_page_length,
    )
    leave_rows = frappe.get_all(
        "Leave Application",
        filters=leave_filters,
        fields=[
            "name",
            "employee",
            "leave_type",
            "from_date",
            "to_date",
            "half_day",
            "half_day_date",
            "total_leave_days",
            "status",
            "modified",
        ],
        order_by="employee asc, from_date asc",
        page_length=query_page_length,
    )

    data = _build_time_and_leave_export(
        attendance_rows=attendance_rows,
        leave_rows=leave_rows,
        from_date=from_date,
        to_date=to_date,
        employee_whitelist=employee_whitelist,
    )

    start = (page - 1) * page_size
    sliced = data[start : start + page_size + 1]
    has_more = len(sliced) > page_size
    return {"data": sliced[:page_size], "meta": _build_meta(page, page_size, has_more)}


@frappe.whitelist()
def notify_worksite_master_change(payload: dict[str, Any] | None = None, **kwargs) -> dict[str, Any]:
    payload = _coerce_payload(payload, kwargs)
    _reject_unknown_keys(payload, {"event_type", "worksite"}, "payload")
    event_type = payload.get("event_type")
    worksite = payload.get("worksite") or {}

    if event_type not in WORKSITE_EVENT_TYPES:
        frappe.throw("event_type must be one of created, updated, deactivated")
    _require_keys(worksite, {"company", "branch", "business_registration_number", "effective_from"}, "worksite")
    _reject_unknown_keys(
        worksite,
        {
            "company",
            "branch",
            "business_registration_number",
            "worksite_code",
            "effective_from",
            "status",
            "modified",
        },
        "worksite",
    )

    return {
        "status": "received",
        "event_type": event_type,
        "worksite": {
            "company": worksite.get("company"),
            "branch": worksite.get("branch"),
            "business_registration_number": worksite.get("business_registration_number"),
            "worksite_code": worksite.get("worksite_code"),
            "effective_from": worksite.get("effective_from"),
            "status": worksite.get("status"),
            "modified": worksite.get("modified"),
        },
        "audit": {
            "resolution_policy": "yaml_wins",
            "queued": False,
            "source": "frappe",
        },
    }


@frappe.whitelist()
def apply_worksite_master_from_yaml(payload: dict[str, Any] | None = None, **kwargs) -> dict[str, Any]:
    payload = _coerce_payload(payload, kwargs)
    _reject_unknown_keys(payload, {"yaml_version", "items"}, "payload")
    yaml_version = payload.get("yaml_version")
    items = payload.get("items")

    if not yaml_version:
        frappe.throw("yaml_version is required")
    if not isinstance(items, list):
        frappe.throw("items must be a list")

    applied = []
    conflicts = []
    for item in items:
        _require_keys(item, {"company", "branch", "business_registration_number", "effective_from"}, "item")
        _reject_unknown_keys(
            item,
            {
                "company",
                "branch",
                "business_registration_number",
                "worksite_code",
                "status",
                "effective_from",
                "effective_to",
                "source_modified",
            },
            "item",
        )
        action, conflict = _apply_worksite_yaml_item(item)
        applied.append(
            {
                "company": item.get("company"),
                "branch": item.get("branch"),
                "action": action,
            }
        )
        if conflict:
            conflicts.append(conflict)

    return {"yaml_version": yaml_version, "applied": applied, "conflicts": conflicts}


@frappe.whitelist()
def import_payroll_result(payload: dict[str, Any] | None = None, **kwargs) -> dict[str, Any]:
    payload = _coerce_payload(payload, kwargs)
    _ensure_no_pii(payload)
    _reject_unknown_keys(
        payload,
        {
            "run_id",
            "employee_id",
            "pay_year_month",
            "salary_slip_external_ref",
            "taxable_items",
            "non_taxable_items",
            "social_insurance_deductions",
            "withholding_tax",
            "gross_pay",
            "total_deduction",
            "net_pay",
            "ruleset_version",
            "engine_version",
        },
        "payload",
    )
    _require_keys(payload, PAYROLL_REQUIRED_FIELDS, "payload")
    if not PAY_YEAR_MONTH_PATTERN.match(str(payload.get("pay_year_month", ""))):
        frappe.throw("pay_year_month must be in YYYY-MM format")
    _validate_payroll_items(payload.get("taxable_items"), "taxable_items")
    _validate_payroll_items(payload.get("non_taxable_items"), "non_taxable_items")
    _validate_required_numeric_mapping(
        payload.get("social_insurance_deductions"), SOCIAL_INSURANCE_FIELDS, "social_insurance_deductions"
    )
    _validate_required_numeric_mapping(payload.get("withholding_tax"), WITHHOLDING_TAX_FIELDS, "withholding_tax")

    with _korea_calc_reference_run_lock(payload["run_id"]):
        if getattr(frappe, "db", None) and frappe.db.exists("Korea Calc Reference", {"run_id": payload["run_id"]}):
            frappe.throw(f"run_id already imported: {payload['run_id']}")

        salary_slip = None
        external_ref = payload.get("salary_slip_external_ref")
        if external_ref and getattr(frappe, "db", None) and frappe.db.exists("Salary Slip", external_ref):
            salary_slip = external_ref

        if salary_slip:
            _record_payroll_import_comment(salary_slip, payload)

        korea_calc_reference = _create_korea_calc_reference(
            kind="payroll",
            payload=payload,
            salary_slip_external_ref=external_ref,
        )

    return {
        "status": "updated" if salary_slip else "received",
        "employee_id": payload["employee_id"],
        "pay_year_month": payload["pay_year_month"],
        "salary_slip": salary_slip,
        "korea_calc_reference": korea_calc_reference,
        "message": "Validated and queued for downstream mapping" if not salary_slip else "Validated and linked to Salary Slip",
    }


@frappe.whitelist()
def import_year_end_settlement_result(payload: dict[str, Any] | None = None, **kwargs) -> dict[str, Any]:
    payload = _coerce_payload(payload, kwargs)
    _ensure_no_pii(payload)
    _reject_unknown_keys(
        payload,
        {
            "run_id",
            "employee_id",
            "settlement_year",
            "settlement_kind",
            "applied_pay_year_month",
            "salary_slip_external_ref",
            "prepaid_tax",
            "determined_tax",
            "adjustment_tax",
            "local_income_tax",
            "engine_version",
            "ruleset_version",
            "note",
        },
        "payload",
    )
    _require_keys(payload, YEAR_END_SETTLEMENT_REQUIRED_FIELDS, "payload")
    if payload.get("settlement_kind") not in SETTLEMENT_KINDS:
        frappe.throw("settlement_kind must be one of annual_february, mid_year_termination")
    if not isinstance(payload.get("settlement_year"), int) or payload.get("settlement_year") < 2000:
        frappe.throw("settlement_year must be an integer greater than or equal to 2000")
    if not PAY_YEAR_MONTH_PATTERN.match(str(payload.get("applied_pay_year_month", ""))):
        frappe.throw("applied_pay_year_month must be in YYYY-MM format")
    for field in ["prepaid_tax", "determined_tax", "adjustment_tax"]:
        _as_float(payload.get(field))
    if payload.get("local_income_tax") is not None:
        _as_float(payload.get("local_income_tax"))

    with _korea_calc_reference_run_lock(payload["run_id"]):
        if getattr(frappe, "db", None) and frappe.db.exists("Korea Calc Reference", {"run_id": payload["run_id"]}):
            frappe.throw(f"run_id already imported: {payload['run_id']}")

        salary_slip = None
        external_ref = payload.get("salary_slip_external_ref")
        if external_ref and getattr(frappe, "db", None) and frappe.db.exists("Salary Slip", external_ref):
            salary_slip = external_ref
        if salary_slip:
            _record_year_end_settlement_comment(salary_slip, payload)

        korea_calc_reference = _create_korea_calc_reference(
            kind="year_end_settlement",
            payload=payload,
            salary_slip_external_ref=external_ref,
        )

    return {
        "status": "updated" if salary_slip else "received",
        "employee_id": payload["employee_id"],
        "settlement_year": payload["settlement_year"],
        "applied_pay_year_month": payload["applied_pay_year_month"],
        "salary_slip": salary_slip,
        "korea_calc_reference": korea_calc_reference,
        "message": "Validated and queued for year-end settlement mapping" if not salary_slip else "Validated and linked to Salary Slip",
    }


@frappe.whitelist()
def import_severance_result(payload: dict[str, Any] | None = None, **kwargs) -> dict[str, Any]:
    payload = _coerce_payload(payload, kwargs)
    _ensure_no_pii(payload)
    _reject_unknown_keys(
        payload,
        {
            "run_id",
            "employee_id",
            "retirement_date",
            "linked_salary_slip",
            "average_wage",
            "service_years",
            "severance_pay",
            "severance_income_tax",
            "local_income_tax",
            "net_pay",
            "engine_version",
            "ruleset_version",
            "note",
        },
        "payload",
    )
    _require_keys(payload, SEVERANCE_REQUIRED_FIELDS, "payload")
    if not DATE_PATTERN.match(str(payload.get("retirement_date", ""))):
        frappe.throw("retirement_date must be in YYYY-MM-DD format")
    for field in ["average_wage", "service_years", "severance_pay", "severance_income_tax", "net_pay"]:
        _as_float(payload.get(field))
    if payload.get("local_income_tax") is not None:
        _as_float(payload.get("local_income_tax"))

    with _korea_calc_reference_run_lock(payload["run_id"]):
        if getattr(frappe, "db", None) and frappe.db.exists("Korea Calc Reference", {"run_id": payload["run_id"]}):
            frappe.throw(f"run_id already imported: {payload['run_id']}")

        linked_salary_slip = None
        external_ref = payload.get("linked_salary_slip")
        if external_ref and getattr(frappe, "db", None) and frappe.db.exists("Salary Slip", external_ref):
            linked_salary_slip = external_ref
        if linked_salary_slip:
            _record_severance_import_comment(linked_salary_slip, payload)

        korea_calc_reference = _create_korea_calc_reference(
            kind="severance",
            payload=payload,
            salary_slip_external_ref=external_ref,
        )

    return {
        "status": "updated" if linked_salary_slip else "received",
        "employee_id": payload["employee_id"],
        "retirement_date": payload["retirement_date"],
        "korea_severance_slip": None,
        "korea_calc_reference": korea_calc_reference,
        "message": "Validated and queued for severance mapping" if not linked_salary_slip else "Validated and linked to Salary Slip",
    }


def _normalize_employee_row(row: dict[str, Any]) -> dict[str, Any]:
    clean = deepcopy(row)
    _ensure_no_pii(clean)
    employment_type = clean.get("employment_type") or "기타"
    if employment_type not in EMPLOYMENT_TYPE_CATEGORY_MAP and employment_type != "기타" and getattr(frappe, "log_error", None):
        frappe.log_error(f"Unknown employment_type from Korea export: {employment_type}")
        employment_type = "기타"

    employment_category = EMPLOYMENT_TYPE_CATEGORY_MAP.get(employment_type, "other")
    if clean.get("visa_status_code"):
        employment_category = "foreign_worker"

    return {
        "employee_id": clean.get("name"),
        "employee_number": clean.get("employee_number") or clean.get("name"),
        "employee_name": clean.get("employee_name") or clean.get("name"),
        "company": clean.get("company"),
        "branch": clean.get("branch"),
        "department": clean.get("department"),
        "designation": clean.get("designation"),
        "employment_type": employment_type,
        "employment_category": employment_category,
        "visa_status_code": clean.get("visa_status_code"),
        "date_of_joining": _stringify_date(clean.get("date_of_joining")),
        "relieving_date": _stringify_date(clean.get("relieving_date")),
        "status": clean.get("status"),
        "modified": _stringify_datetime(clean.get("modified")),
    }


def _build_time_and_leave_export(
    attendance_rows: list[dict[str, Any]],
    leave_rows: list[dict[str, Any]],
    from_date: str,
    to_date: str,
    employee_whitelist: set[str] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for row in attendance_rows:
        employee = row.get("employee")
        if not employee or (employee_whitelist is not None and employee not in employee_whitelist):
            continue
        target = grouped.setdefault(employee, _new_time_and_leave_bucket(employee, from_date, to_date))
        normalized = _normalize_attendance_row(row)
        target["attendance_records"].append(normalized)
        target["work_time_summary"]["regular_hours_total"] += normalized["regular_hours"]
        target["work_time_summary"]["overtime_hours_total"] += normalized["overtime_hours"]
        target["work_time_summary"]["night_hours_total"] += normalized["night_hours"]
        target["work_time_summary"]["holiday_hours_total"] += normalized["holiday_hours"]

    for row in leave_rows:
        employee = row.get("employee")
        if not employee or (employee_whitelist is not None and employee not in employee_whitelist):
            continue
        target = grouped.setdefault(employee, _new_time_and_leave_bucket(employee, from_date, to_date))
        target["leave_records"].append(_normalize_leave_row(row))

    return [grouped[key] for key in sorted(grouped)]


def _new_time_and_leave_bucket(employee: str, from_date: str, to_date: str) -> dict[str, Any]:
    return {
        "employee_id": employee,
        "period": {"from_date": from_date, "to_date": to_date},
        "attendance_records": [],
        "leave_records": [],
        "work_time_summary": {
            "regular_hours_total": 0.0,
            "overtime_hours_total": 0.0,
            "night_hours_total": 0.0,
            "holiday_hours_total": 0.0,
        },
    }


def _normalize_attendance_row(row: dict[str, Any]) -> dict[str, Any]:
    regular_hours = _as_float(row.get("regular_hours", row.get("working_hours", 0)))
    overtime_hours = _as_float(row.get("overtime_hours", row.get("custom_overtime_hours", 0)))
    night_hours = _as_float(row.get("night_hours", row.get("custom_night_hours", 0)))
    holiday_hours = _as_float(row.get("holiday_hours", row.get("custom_holiday_hours", 0)))

    return {
        "attendance_id": row.get("name"),
        "attendance_date": _stringify_date(row.get("attendance_date")),
        "status": row.get("status"),
        "shift_type": row.get("shift"),
        "in_time": _stringify_datetime(row.get("in_time")),
        "out_time": _stringify_datetime(row.get("out_time")),
        "regular_hours": regular_hours,
        "overtime_hours": overtime_hours,
        "night_hours": night_hours,
        "holiday_hours": holiday_hours,
        "modified": _stringify_datetime(row.get("modified")),
    }


def _normalize_leave_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "leave_application_id": row.get("name"),
        "leave_type": row.get("leave_type"),
        "from_date": _stringify_date(row.get("from_date")),
        "to_date": _stringify_date(row.get("to_date")),
        "half_day": bool(row.get("half_day")),
        "half_day_date": _stringify_date(row.get("half_day_date")),
        "total_leave_days": _as_float(row.get("total_leave_days", 0)),
        "status": row.get("status"),
        "modified": _stringify_datetime(row.get("modified")),
    }


def _record_payroll_import_comment(salary_slip: str, payload: dict[str, Any]) -> None:
    if not getattr(frappe, "get_doc", None):
        return

    comment = {
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Salary Slip",
        "reference_name": salary_slip,
        "content": (
            f"Korea payroll import received: run_id={payload['run_id']}, "
            f"employee_id={payload['employee_id']}, pay_year_month={payload['pay_year_month']}, "
            f"net_pay={payload['net_pay']}"
        ),
    }
    try:
        frappe.get_doc(comment).insert(ignore_permissions=True)
    except Exception:
        if getattr(frappe, "log_error", None):
            frappe.log_error("Failed to persist Korea payroll import comment")


def _record_year_end_settlement_comment(salary_slip: str, payload: dict[str, Any]) -> None:
    _insert_salary_slip_comment(
        salary_slip,
        (
            f"Korea year-end settlement import received: run_id={payload['run_id']}, "
            f"employee_id={payload['employee_id']}, settlement_year={payload['settlement_year']}, "
            f"applied_pay_year_month={payload['applied_pay_year_month']}, adjustment_tax={payload['adjustment_tax']}"
        ),
        "Failed to persist Korea year-end settlement import comment",
    )


def _record_severance_import_comment(salary_slip: str, payload: dict[str, Any]) -> None:
    _insert_salary_slip_comment(
        salary_slip,
        (
            f"Korea severance import received: run_id={payload['run_id']}, "
            f"employee_id={payload['employee_id']}, retirement_date={payload['retirement_date']}, "
            f"net_pay={payload['net_pay']}"
        ),
        "Failed to persist Korea severance import comment",
    )


def _insert_salary_slip_comment(salary_slip: str, content: str, error_message: str) -> None:
    if not getattr(frappe, "get_doc", None):
        return

    comment = {
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Salary Slip",
        "reference_name": salary_slip,
        "content": content,
    }
    try:
        frappe.get_doc(comment).insert(ignore_permissions=True)
    except Exception:
        if getattr(frappe, "log_error", None):
            frappe.log_error(error_message)


@contextmanager
def _worksite_sync_lock(branch_name: str):
    lock_key = f"korea-worksite-sync:{branch_name}"
    cache_factory = getattr(frappe, "cache", None)
    if callable(cache_factory):
        cache = cache_factory()
        cache_lock = getattr(cache, "lock", None)
        if callable(cache_lock):
            with cache_lock(lock_key, timeout=LOCK_TTL_SECONDS, **_nonblocking_lock_kwargs(cache_lock)):
                yield
            return

    utils = getattr(frappe, "utils", None)
    lock_module = getattr(utils, "lock", None) if utils else None
    create_lock = getattr(lock_module, "create_lock", None) if lock_module else None
    if callable(create_lock):
        parameters = inspect.signature(create_lock).parameters
        kwargs = _nonblocking_lock_kwargs(create_lock)
        if "timeout" in parameters:
            kwargs["timeout"] = LOCK_TTL_SECONDS
        elif "expire" in parameters:
            kwargs["expire"] = LOCK_TTL_SECONDS
        elif "expires" in parameters:
            kwargs["expires"] = LOCK_TTL_SECONDS
        with create_lock(lock_key, **kwargs):
            yield
        return

    frappe.throw("No supported Frappe lock primitive available for worksite sync")


def _nonblocking_lock_kwargs(lock_factory: Any) -> dict[str, Any]:
    try:
        parameters = inspect.signature(lock_factory).parameters
    except (TypeError, ValueError):
        return {"blocking_timeout": 0}
    if "blocking_timeout" in parameters:
        return {"blocking_timeout": 0}
    if "blocking" in parameters:
        return {"blocking": False}
    if "wait" in parameters:
        return {"wait": False}
    return {"blocking_timeout": 0}


def _is_frappe_lock_error(exc: Exception) -> bool:
    lock_error = getattr(frappe, "LockError", None)
    if lock_error and isinstance(exc, lock_error):
        return True

    exceptions_module = getattr(frappe, "exceptions", None)
    fallback_lock_error = getattr(exceptions_module, "LockError", None) if exceptions_module else None
    if fallback_lock_error and isinstance(exc, fallback_lock_error):
        return True

    return exc.__class__.__name__ == "LockError"


def _apply_worksite_yaml_item(item: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    branch_name = item["branch"]
    try:
        with _worksite_sync_lock(branch_name):
            branch_exists = bool(getattr(frappe.db, "exists", lambda *args, **kwargs: None)("Branch", branch_name))
            current = _get_branch_worksite_state(branch_name) if branch_exists else {}
            desired = _build_desired_worksite_state(item)
            field_map = _get_worksite_field_map()
            changed_fields = [
                field
                for field, value in desired.items()
                if field != "last_sync_payload" and current.get(field) != value
            ]

            if not branch_exists:
                _persist_branch_worksite_state(branch_name, item["company"], desired)
                return "created", None
            if not changed_fields:
                return "ignored", None

            desired["sync_status"] = "conflict_detected"
            _persist_branch_worksite_state(branch_name, item["company"], desired)
            detail = ", ".join(sorted(field_map.get(field, field) for field in changed_fields))
            return (
                "updated",
                {
                    "company": item.get("company"),
                    "branch": branch_name,
                    "resolution": "yaml_wins",
                    "detail": detail,
                },
            )
    except Exception as exc:
        if _is_frappe_lock_error(exc):
            return (
                "rejected_locked",
                {
                    "company": item.get("company"),
                    "branch": branch_name,
                    "reason": "concurrent_sync_in_progress",
                },
            )
        raise


def _build_desired_worksite_state(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "business_registration_number": item.get("business_registration_number"),
        "worksite_code": item.get("worksite_code"),
        "status": item.get("status"),
        "effective_from": item.get("effective_from"),
        "effective_to": item.get("effective_to"),
        "source_modified": item.get("source_modified"),
        "sync_status": "synced",
        "last_sync_payload": json.dumps(item, ensure_ascii=False, sort_keys=True),
    }


def _get_branch_worksite_state(branch_name: str) -> dict[str, Any]:
    field_map = _get_worksite_field_map()
    state = {}
    getter = getattr(frappe.db, "get_value", None)
    if not getter:
        return state
    for logical_field, actual_field in field_map.items():
        state[logical_field] = getter("Branch", branch_name, actual_field)
    return state


def _persist_branch_worksite_state(branch_name: str, company: str, state: dict[str, Any]) -> None:
    field_map = _get_worksite_field_map()
    payload = {"company": company}
    for logical_field, value in state.items():
        actual_field = field_map.get(logical_field)
        if actual_field:
            payload[actual_field] = value

    exists = bool(getattr(frappe.db, "exists", lambda *args, **kwargs: None)("Branch", branch_name))
    if not exists and getattr(frappe, "get_doc", None):
        doc_payload = {"doctype": "Branch", "name": branch_name, "branch": branch_name, **payload}
        try:
            frappe.get_doc(doc_payload).insert(ignore_permissions=True)
            return
        except Exception:
            if getattr(frappe, "log_error", None):
                frappe.log_error(f"Failed to insert Branch for worksite sync: {branch_name}")

    setter = getattr(frappe.db, "set_value", None)
    if setter:
        setter("Branch", branch_name, payload)


def _get_worksite_field_map() -> dict[str, str]:
    field_map = {}
    for logical_field, candidates in WORKSITE_FIELD_CANDIDATES.items():
        available = _get_optional_fields("Branch", candidates)
        if available:
            field_map[logical_field] = available[0]
    return field_map


def _get_optional_fields(doctype: str, candidates: list[str] | None = None) -> list[str]:
    db = getattr(frappe, "db", None)
    if not db or not hasattr(db, "get_table_columns"):
        return candidates or []

    columns = set(db.get_table_columns(doctype) or [])
    candidates = candidates or [
        "working_hours",
        "regular_hours",
        "overtime_hours",
        "night_hours",
        "holiday_hours",
        "custom_overtime_hours",
        "custom_night_hours",
        "custom_holiday_hours",
        "in_time",
        "out_time",
    ]
    return [field for field in candidates if field in columns]


def _coerce_payload(payload: dict[str, Any] | None, kwargs: dict[str, Any]) -> dict[str, Any]:
    if payload is not None:
        return payload
    if kwargs:
        return kwargs
    if getattr(frappe, "local", None) and getattr(frappe.local, "form_dict", None):
        form_dict = dict(frappe.local.form_dict)
        if len(form_dict) == 1 and "payload" in form_dict and isinstance(form_dict["payload"], str):
            return json.loads(form_dict["payload"])
        return form_dict
    return {}


def _normalize_pagination(page: int | str, page_size: int | str) -> tuple[int, int]:
    try:
        page = max(int(page), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(page_size)
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    return page, page_size


def _build_meta(page: int, page_size: int, has_more: bool) -> dict[str, Any]:
    return {"page": page, "page_size": page_size, "has_more": has_more}


def _bounded_query_page_length(page_size: int) -> int:
    return min(max(page_size, DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE) + 1


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _ensure_no_pii(payload: Any) -> None:
    if isinstance(payload, dict):
        keys = set(payload)
        blocked = keys & BLOCKED_PII_FIELDS
        if blocked:
            frappe.throw(f"PII fields are not allowed: {', '.join(sorted(blocked))}")
        for value in payload.values():
            _ensure_no_pii(value)
    elif isinstance(payload, list):
        for item in payload:
            _ensure_no_pii(item)


def _require_keys(payload: Any, required_keys: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        frappe.throw(f"{label} must be an object")
    missing = [key for key in sorted(required_keys) if key not in payload or payload.get(key) in (None, "")]
    if missing:
        frappe.throw(f"{label} is missing required fields: {', '.join(missing)}")


def _reject_unknown_keys(payload: Any, allowed_keys: set[str], label: str) -> None:
    if not isinstance(payload, dict):
        frappe.throw(f"{label} must be an object")
    unknown = sorted(set(payload) - allowed_keys)
    if unknown:
        frappe.throw(f"{label} contains unsupported fields: {', '.join(unknown)}")


def _validate_payroll_items(items: Any, label: str) -> None:
    if not isinstance(items, list):
        frappe.throw(f"{label} must be a list")
    for item in items:
        _require_keys(item, {"code", "label", "amount"}, label)
        _reject_unknown_keys(item, {"code", "label", "amount"}, label)
        _as_float(item.get("amount"))


def _validate_required_numeric_mapping(payload: Any, required_keys: set[str], label: str) -> None:
    _require_keys(payload, required_keys, label)
    _reject_unknown_keys(payload, required_keys, label)
    for key in required_keys:
        _as_float(payload.get(key))


@contextmanager
def _korea_calc_reference_run_lock(run_id: str):
    db = getattr(frappe, "db", None)
    if not db or not hasattr(db, "sql"):
        yield
        return

    lock_name = f"korea_calc_reference:{run_id}"
    lock_result = db.sql("SELECT GET_LOCK(%s, %s)", (lock_name, 5))
    if _extract_lock_scalar(lock_result) != 1:
        frappe.throw(f"Could not acquire import lock for run_id: {run_id}")

    try:
        yield
    finally:
        db.sql("SELECT RELEASE_LOCK(%s)", (lock_name,))


def _extract_lock_scalar(result: Any) -> Any:
    if isinstance(result, (list, tuple)) and result:
        first = result[0]
        if isinstance(first, (list, tuple)) and first:
            return first[0]
        return first
    return result


def _create_korea_calc_reference(
    kind: str,
    payload: dict[str, Any],
    salary_slip_external_ref: str | None = None,
) -> str:
    doc_payload = {
        "doctype": "Korea Calc Reference",
        "run_id": payload["run_id"],
        "kind": kind,
        "employee_id": payload["employee_id"],
        "pay_year_month": payload.get("pay_year_month"),
        "applied_pay_year_month": payload.get("applied_pay_year_month"),
        "retirement_date": payload.get("retirement_date"),
        "salary_slip_external_ref": salary_slip_external_ref,
        "engine_version": payload.get("engine_version"),
        "ruleset_version": payload.get("ruleset_version"),
        "import_payload": _serialize_import_payload(payload),
        "imported_at": _current_timestamp(),
        "imported_by": _current_user(),
    }
    doc = frappe.get_doc(doc_payload).insert(ignore_permissions=True)
    return getattr(doc, "name", payload["run_id"])


def _serialize_import_payload(payload: dict[str, Any]) -> str:
    clean_payload = deepcopy(payload)
    _ensure_no_pii(clean_payload)
    return json.dumps(clean_payload, ensure_ascii=False, sort_keys=True)


def _current_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")


def _current_user() -> str | None:
    session = getattr(frappe, "session", None)
    return getattr(session, "user", None)


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        frappe.throw(f"Invalid numeric value: {value}")
        raise RuntimeError(f"frappe.throw returned unexpectedly for invalid numeric value: {value}")


def _stringify_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)


def _stringify_datetime(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    return str(value)
