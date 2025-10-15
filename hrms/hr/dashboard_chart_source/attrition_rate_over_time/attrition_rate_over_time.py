# hrms/hr/dashboard_chart_source/attrition_rate_over_time/attrition_rate_over_time.py

import frappe
from frappe.utils import nowdate

def get(filters):
    """
    Returns data for the 'Attrition Rate Over Time' chart.
    """
    # Query all employee separations
    separations = frappe.get_all(
        "Employee Separation",
        fields=["resignation_letter_date"],
        filters={"docstatus": 1} # Only count submitted separations
    )

    if not separations:
        return {
            "labels": [],
            "datasets": []
        }

    # Process data to count separations per month
    monthly_counts = {}
    for sep in separations:
        if sep.resignation_letter_date:
            month = sep.resignation_letter_date.strftime("%Y-%m")
            monthly_counts[month] = monthly_counts.get(month, 0) + 1

    # Sort by month and prepare for the chart
    sorted_months = sorted(monthly_counts.keys())
    labels = [frappe.utils.formatdate(month + "-01", "MMM YYYY") for month in sorted_months]
    values = [monthly_counts[month] for month in sorted_months]

    return {
        "labels": labels,
        "datasets": [
            {
                "name": "Number of Separations",
                "values": values
            }
        ]
    }
