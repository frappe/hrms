# hrms/hr/dashboard_chart_source/attrition_by_designation/attrition_by_designation.py

import frappe

def get(filters):
    """
    Returns data for the 'Attrition by Designation' chart.
    """
    separations = frappe.get_all(
        "Employee Separation",
        fields=["designation"],
        filters={"docstatus": 1}
    )

    if not separations:
        return {"labels": [], "datasets": []}

    # Process data to count separations per designation
    desig_counts = {}
    for sep in separations:
        if sep.designation:
            desig_counts[sep.designation] = desig_counts.get(sep.designation, 0) + 1

    # Prepare for the chart
    labels = list(desig_counts.keys())
    values = list(desig_counts.values())

    return {
        "labels": labels,
        "datasets": [
            {
                "name": "Separations by Designation",
                "values": values
            }
        ]
    }
