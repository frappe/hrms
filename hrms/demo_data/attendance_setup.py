"""
Attendance Setup - Demo Data Generator for HRMS
Creates Employee Checkin and Attendance records from JSON data file

Author: amezasor
Version: 1.0.0

Usage: 
    bench --site [sitename] execute demo_data.attendance_setup.create_attendance_data
    Or with custom JSON path:
    bench --site [sitename] execute demo_data.attendance_setup.create_attendance_data --kwargs '{"attendance_path": "/path/to/file.json"}'
"""

import os
import json
import frappe
from datetime import datetime
from hrms.demo_data.utils import load_data


def create_attendance_data(company="NovaSoft", attendance_path=None):
    """
    Create Employee Checkin and Attendance records from JSON file
    
    :param company: Company name for attendance records
    :param attendance_path: Path to JSON file (defaults to demo_data/employee_attendance.json)
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Creating Attendance Data for Company: {company}")
    print(f"{'='*60}\n")
    
    # Load attendance data from JSON
    records_list = load_data(attendance_path, key="attendance_records")

    print(f"📋 Loading attendance records'")
    print(f"   Employees: {len(records_list)}\n")
    
    checkin_count = 0
    attendance_count = 0
    errors = []
    
    for emp_data in records_list:
        emp_id = emp_data.get("employee_id")
        emp_name = emp_data.get("employee_name")
        default_shift = emp_data.get("shift")
        default_status = emp_data.get("status", "Present")
        
        print(f"  Processing: {emp_name} ({emp_id})")
        
        # Verify employee exists
        if not frappe.db.exists("Employee", emp_id):
            errors.append(f"{emp_name}: Employee {emp_id} not found")
            print(f"    ⚠ Employee not found: {emp_id}")
            continue
        
        for record in emp_data.get("records", []):
            date_str = record.get("date")
            checkin_time = record.get("checkin")
            checkout_time = record.get("checkout")
            status = record.get("status_override", default_status)
            
            # Create check-in record (if checkin time provided)
            if checkin_time:
                checkin_datetime = f"{date_str} {checkin_time}"
                try:
                    checkin = create_employee_checkin(
                        employee=emp_id,
                        time=checkin_datetime,
                        log_type="IN"
                    )
                    if checkin:
                        checkin_count += 1
                        print(f"    ✓ Checkin: {date_str} {checkin_time}")
                except Exception as e:
                    errors.append(f"{emp_name} IN ({date_str}): {str(e)[:50]}")
                    print(f"    ⚠ Checkin error: {str(e)[:50]}")
            
            # Create check-out record (if checkout time provided)
            if checkout_time:
                checkout_datetime = f"{date_str} {checkout_time}"
                try:
                    checkout = create_employee_checkin(
                        employee=emp_id,
                        time=checkout_datetime,
                        log_type="OUT"
                    )
                    if checkout:
                        checkin_count += 1
                        print(f"    ✓ Checkout: {date_str} {checkout_time}")
                except Exception as e:
                    errors.append(f"{emp_name} OUT ({date_str}): {str(e)[:50]}")
                    print(f"    ⚠ Checkout error: {str(e)[:50]}")
            
            # Create Attendance record
            try:
                in_time = f"{date_str} {checkin_time}" if checkin_time else None
                out_time = f"{date_str} {checkout_time}" if checkout_time else None
                
                # Get late_entry and early_exit flags from record
                late_entry = record.get("late_entry", False)
                early_exit = record.get("early_exit", False)
            
                attendance = create_attendance_record(
                    employee=emp_id,
                    attendance_date=date_str,
                    status=status,
                    company=company,
                    shift=default_shift,
                    in_time=in_time,
                    out_time=out_time,
                    late_entry=late_entry,
                    early_exit=early_exit
                )
                if attendance:
                    attendance_count += 1
                    flags = []
                    if late_entry:
                        flags.append("LATE")
                    if early_exit:
                        flags.append("EARLY EXIT")
                    flag_str = f" [{', '.join(flags)}]" if flags else ""
                    print(f"    ✓ Attendance: {date_str} - {status}{flag_str}")
            except Exception as e:
                errors.append(f"{emp_name} Attendance ({date_str}): {str(e)[:50]}")
                print(f"    ⚠ Attendance error: {str(e)[:50]}")
        
        print()
    
    frappe.db.commit()
    
    # Print summary
    print(f"\n{'='*60}")
    print("✅ Attendance Data Creation Complete!")
    print(f"{'='*60}")
    print(f"\n  ✓ Created {checkin_count} Employee Checkin records")
    print(f"  ✓ Created {attendance_count} Attendance records")
    
    if errors:
        print(f"\n  ⚠ {len(errors)} errors:")
        for err in errors[:10]:
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")
    
    print(f"\n{'='*60}\n")
    
    return {
        "checkins": checkin_count,
        "attendance": attendance_count,
        "errors": len(errors)
    }


# def load_attendance_data(attendance_path=None):
#     """Load attendance data from JSON file"""
#     if attendance_path is None:
#         # Default path relative to the demo_data directory
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         attendance_path = os.path.join(current_dir, "employee_attendance.json")
    
#     print(f"📄 Loading attendance data from: {attendance_path}")
    
#     try:
#         with open(attendance_path, 'r') as f:
#             data = json.load(f)
#         print(f"  ✓ Loaded {len(data.get('attendance_records', []))} employee records\n")
#         return data
#     except FileNotFoundError:
#         print(f"  ⚠ File not found: {attendance_path}")
#         return None
#     except json.JSONDecodeError as e:
#         print(f"  ⚠ Invalid JSON: {str(e)}")
#         return None


def create_employee_checkin(employee, time, log_type):
    """
    Create an Employee Checkin record
    
    :param employee: Employee ID (e.g., "HR-EMP-00004")
    :param time: Datetime string (e.g., "2025-11-03 07:00:00")
    :param log_type: "IN" or "OUT"
    :return: Created document or None
    """
    # Check if checkin already exists
    existing = frappe.db.exists("Employee Checkin", {
        "employee": employee,
        "time": time,
        "log_type": log_type
    })
    
    if existing:
        print(f"    ↻ Checkin already exists: {log_type} at {time}")
        return None
    
    checkin = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee,
        "time": time,
        "log_type": log_type,
        "skip_auto_attendance": 1  # We create attendance manually
    })
    
    checkin.flags.ignore_validate = True
    checkin.insert(ignore_permissions=True)
    
    return checkin

def create_attendance_record(employee, attendance_date, status, company, shift=None, in_time=None, out_time=None, late_entry=False, early_exit=False):
    """
    Create an Attendance record
    
    :param employee: Employee ID
    :param attendance_date: Date string (e.g., "2025-11-03")
    :param status: "Present", "Absent", "Work From Home", etc.
    :param company: Company name
    :param shift: Shift Type name
    :param in_time: Check-in datetime
    :param out_time: Check-out datetime
    :param late_entry: Boolean - mark as late entry
    :param early_exit: Boolean - mark as early exit
    :return: Created document or None
    """
    # Check if attendance already exists
    existing = frappe.db.exists("Attendance", {
        "employee": employee,
        "attendance_date": attendance_date
    })
    
    if existing:
        print(f"    ↻ Attendance already exists for {attendance_date}")
        return None
    
    attendance_doc = {
        "doctype": "Attendance",
        "employee": employee,
        "attendance_date": attendance_date,
        "status": status,
        "company": company
    }
    
    if shift:
        attendance_doc["shift"] = shift
    
    if in_time:
        attendance_doc["in_time"] = in_time
    
    if out_time:
        attendance_doc["out_time"] = out_time
    
    # Set late entry and early exit flags
    if late_entry:
        attendance_doc["late_entry"] = 1
    
    if early_exit:
        attendance_doc["early_exit"] = 1
    
    # Calculate working hours if both in and out times are provided
    if in_time and out_time and status not in ["Absent"]:
        try:
            in_dt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S")
            out_dt = datetime.strptime(out_time, "%Y-%m-%d %H:%M:%S")
            working_hours = (out_dt - in_dt).total_seconds() / 3600
            attendance_doc["working_hours"] = working_hours
        except Exception:
            pass
    
    attendance = frappe.get_doc(attendance_doc)
    attendance.flags.ignore_mandatory = True
    attendance.insert(ignore_permissions=True)
    # Reload to get fresh document with correct modified timestamp
    # This prevents "has been modified" errors in bulk operations
    attendance.reload()    
    attendance.submit()
    
    return attendance


def clear_attendance_data(company="NovaSoft", attendance_path=None):
    """
    Clear existing attendance data for employees in the JSON file
    USE WITH CAUTION - This will delete data!
    
    Usage: bench --site [sitename] execute hrms.demo_data.attendance_setup.clear_attendance_data
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"⚠️  Clearing Attendance Data for Company: {company}")
    print(f"{'='*60}\n")
    
    # Load attendance data to get employee IDs and dates
    records_list = load_data(attendance_path, key="attendance_records")
    if not records_list:
        print("  ⚠ No attendance data found. Exiting.")
        return
    
    print(f"📋 Found {len(records_list)} employees in JSON file\n")
    print("⚠️  Starting deletion process...\n")
    
    deleted_attendance = 0
    deleted_checkins = 0
    
    for emp_data in records_list:
        emp_id = emp_data.get("employee_id")
        emp_name = emp_data.get("employee_name")
        
        print(f"  Processing: {emp_name} ({emp_id})")
        
        for record in emp_data.get("records", []):
            date_str = record.get("date")
            
            # Cancel and delete attendance records
            attendance_list = frappe.get_all("Attendance", filters={
                "employee": emp_id,
                "attendance_date": date_str
            })
            for att in attendance_list:
                try:
                    doc = frappe.get_doc("Attendance", att.name)
                    if doc.docstatus == 1:
                        doc.cancel()
                    frappe.delete_doc("Attendance", att.name, force=True)
                    deleted_attendance += 1
                    print(f"    ✓ Deleted attendance: {date_str}")
                except Exception as e:
                    print(f"    ⚠ Error deleting attendance {att.name}: {str(e)[:50]}")
            
                # Delete checkin records
                checkin_list = frappe.get_all("Employee Checkin", filters={
                    "employee": emp_id,
                    "time": ["between", [f"{date_str} 00:00:00", f"{date_str} 23:59:59"]]
                })
                for checkin in checkin_list:
                    try:
                        frappe.delete_doc("Employee Checkin", checkin.name, force=True)
                        deleted_checkins += 1
                    except Exception as e:
                        print(f"    ⚠ Error deleting checkin {checkin.name}: {str(e)[:50]}")
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Attendance Data Deletion Complete!")
    print(f"{'='*60}")
    print(f"\n  ✓ Deleted {deleted_attendance} Attendance records")
    print(f"  ✓ Deleted {deleted_checkins} Employee Checkin records")
    print(f"\n{'='*60}\n")
    
    return {
        "attendance": deleted_attendance,
        "checkins": deleted_checkins
    }