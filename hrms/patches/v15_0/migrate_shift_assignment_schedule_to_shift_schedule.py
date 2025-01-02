import frappe
from hrms.hr.doctype.shift_schedule.shift_schedule import get_or_insert_shift_schedule

def execute():
    fields = ["name", "shift_type", "frequency", "employee", "shift_status", "enabled", "create_shifts_after"]
    
    try:
        shift_assignment_schedules = frappe.get_all("Shift Assignment Schedule", fields=fields)
    except frappe.DoesNotExistError:
        frappe.log_error("Shift Assignment Schedule DocType does not exist. Migration skipped for this DocType.", "Migration Warning")
        return  

    for doc in shift_assignment_schedules:
        try:
            repeat_on_days = frappe.get_all(
                "Assignment Rule Day", {"parent": doc.name}, pluck="day", distinct=True
            )
            shift_schedule_name = get_or_insert_shift_schedule(doc.shift_type, doc.frequency, repeat_on_days)

            schedule_assignment = frappe.get_doc(
                {
                    "doctype": "Shift Schedule Assignment",
                    "shift_schedule": shift_schedule_name,
                    "employee": doc.employee,
                    "shift_status": doc.shift_status,
                    "enabled": doc.enabled,
                    "create_shifts_after": doc.create_shifts_after,
                }
            ).insert()

            for d in frappe.get_all("Shift Assignment", filters={"schedule": doc.name}, pluck="name"):
                frappe.db.set_value("Shift Assignment", d, "shift_schedule_assignment", schedule_assignment.name)

        except Exception as e:
            frappe.log_error(f"Error processing Shift Assignment Schedule {doc.name}: {str(e)}", "Migration Error")
