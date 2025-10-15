# hrms/utils/kpi_engine.py

import frappe
from frappe.utils import nowdate, add_months, get_first_day, get_last_day, getdate

def calculate_and_store_kpis_for_period(period_start=None, period_end=None):
    """
    Calculates and stores foundational KPIs for all employees for a given period.
    If no period is provided, it defaults to the previous month.
    """
    if not period_start or not period_end:
        # Default to the previous month
        last_month = add_months(getdate(nowdate()), -1)
        period_start = get_first_day(last_month)
        period_end = get_last_day(last_month)

    period_name = getdate(period_start).strftime("%Y-%m")

    employees = frappe.get_all("Employee", fields=["name"])

    for emp in employees:
        employee = emp['name']

        # Get all tasks completed by the employee in the period
        # Note: We'd need a 'completion_date' field to do this accurately.
        # For now, we'll filter by due_date as a proxy.
        completed_tasks = frappe.get_all(
            "Task",
            filters={
                "owner": employee,
                "status": "Done",
                "due_date": ["between", [period_start, period_end]]
            },
            fields=["name", "due_date", "estimated_time", "actual_time"]
        )

        if not completed_tasks:
            continue

        # --- Calculate KPIs ---

        # 1. Task Completion Rate (simple count for now)
        # A more accurate version would compare against assigned tasks.
        task_completion_count = len(completed_tasks)

        # 2. On-Time Delivery %
        on_time_tasks = [t for t in completed_tasks if t.get('completion_date') and t.get('due_date') and getdate(t['completion_date']) <= getdate(t['due_date'])]
        on_time_delivery_pct = (len(on_time_tasks) / len(completed_tasks)) * 100 if completed_tasks else 0

        # 3. Effort Accuracy
        total_estimated = sum(t['estimated_time'] for t in completed_tasks if t['estimated_time'])
        total_actual = sum(t['actual_time'] for t in completed_tasks if t['actual_time'])
        effort_accuracy = (total_estimated / total_actual) * 100 if total_actual > 0 else 0

        # --- Store KPIs ---
        kpi_map = {
            "Task Completion Count": task_completion_count,
            "On-Time Delivery %": on_time_delivery_pct,
            "Effort Accuracy": effort_accuracy,
        }

        for kpi_name, value in kpi_map.items():
            kpi_doc = frappe.new_doc("KPI Value")
            kpi_doc.employee = employee
            kpi_doc.kpi_name = kpi_name
            kpi_doc.period = period_name
            kpi_doc.value = value
            # Insert with a unique key to prevent duplicates if the job runs multiple times
            try:
                kpi_doc.insert(ignore_permissions=True)
            except frappe.UniqueValidationError:
                # KPI for this employee/period/name already exists, just log it.
                print(f"KPI '{kpi_name}' for {employee} on {period_name} already exists.")

    frappe.db.commit()
    print("KPI calculation complete.")

# We need a wrapper for the scheduled job
def calculate_kpis_for_previous_month():
    calculate_and_store_kpis_for_period()
