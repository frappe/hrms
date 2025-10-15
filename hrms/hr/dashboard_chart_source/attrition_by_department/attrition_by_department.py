# hrms/hr/dashboard_chart_source/attrition_by_department/attrition_by_department.py

import frappe

def get(filters):
    """
    Returns data for the 'Attrition by Department' chart.
    """
    separations = frappe.get_all(
        "Employee Separation",
        fields=["department"],
        filters={"docstatus": 1}
    )

    if not separations:
        return {"labels": [], "datasets": []}

    # Process data to count separations per department
    dept_counts = {}
    for sep in separations:
        if sep.department:
            dept_counts[sep.department] = dept_counts.get(sep.department, 0) + 1

    # Prepare for the chart
    labels = list(dept_counts.keys())
    values = list(dept_counts.values())

    return {
        "labels": labels,
        "datasets": [
            {
                "name": "Separations by Department",
                "values": values
            }
        ]
    }
