def get_shift(employee, date):
    return frappe.db.get_value(
        "Shift Assignment",
        {
            "employee": employee,
            "start_date": ["<=", date],
            "end_date": [">=", date],
            "docstatus": 1
        },
        "shift_type"
    )
