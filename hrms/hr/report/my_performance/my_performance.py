# hrms/hr/report/my_performance/my_performance.py

import frappe
import pandas as pd

def execute(filters=None):
    columns, data = [], []

    current_user = frappe.session.user
    employee = frappe.db.get_value("Employee", {"user_id": current_user}, "name")

    if not employee:
        frappe.msgprint("No employee found for the current user.")
        return columns, data

    kpi_data = frappe.get_all(
        "KPI Value",
        filters={"employee": employee},
        fields=["kpi_name", "period", "value"],
        order_by="period asc"
    )

    if not kpi_data:
        frappe.msgprint("No performance data found for you yet.")
        return columns, data

    # Pivot the data using pandas
    df = pd.DataFrame(kpi_data)
    pivot_df = df.pivot(index='period', columns='kpi_name', values='value').reset_index()

    # Define columns based on the pivoted data
    columns = [{"label": "Period", "fieldname": "period", "fieldtype": "Data", "width": 120}]
    for col in pivot_df.columns:
        if col != 'period':
            columns.append({"label": col, "fieldname": col, "fieldtype": "Float", "width": 150})

    # Convert DataFrame to a list of dictionaries for the report
    data = pivot_df.to_dict(orient='records')

    return columns, data
