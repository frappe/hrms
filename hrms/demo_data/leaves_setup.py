"""
Leave Management Setup - Demo Data Generator for HRMS

Configures leave types with company policies:
- Removes default leave types
- Configures Sick Leave with carry forward
- Configures Compensatory Off (earned)
- Configures Leave Without Pay (LWP)
- Adds Vacation Leave with encashment

Author: amezasor
Version: 1.0.0

Usage: 
    bench --site [sitename] execute hrms.demo_data.leaves_mgm_setup.configure_leave_management
"""
from operator import le
import os
import json
import frappe
from hrms.demo_data.utils import load_data


def configure_leave_management(company="NovaSoft", leaves_path="employee_leaves.json"):
    """
    Central method to configure leave management for the company
    This function will handle various leave management configurations including:
    - Leave types setup
    - Leave period setup
    - Leave policies
    - Leave policy assignments
    - Compensatory leave requests for Memorial Day
    - Leave applications
    
    :param company: Company name for leave configuration
    :param leaves_path: Path to the leave applications JSON file
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Configuring Leave Management for Company: {company}")
    print(f"{'='*60}\n")

    # Step 0: Configure Holiday List -> this is done in the company_setup.py file
    
    # Step 1: Configure Leave Types: 1) Remove unwanted leave types, 2) Configure leave types
    print("Step 1: Configuring Leave Types...")    
    leave_types_result = leave_types_setup(leaves_path)

    # Step 2: Configure Leave Period
    print("\nStep 2: Configuring Leave Period...")
    leave_period_name = leave_period_setup(company, leaves_path)
    
    # Step 3: Create Leave Policy
    print("\nStep 3: Creating Leave Policy...")
    policy_name = create_leave_policy(company, leaves_path)
    
    # Step 4: Assign Leave Policy to Employees
    if policy_name and leave_period_name:
        print("\nStep 4: Assigning Leave Policy to Employees...")
        assign_leave_policy_to_employees(company, leave_period_name, leaves_path)
    else:
        print("\n⚠ Skipping Step 4: Policy or Leave Period not created")
    
    # Step 5: Create Compensatory Leave Requests for Memorial Day
    print("\nStep 5: Creating Compensatory Leave Requests for Memorial Day...")
    comp_result = create_compensatory_leave_requests_for_memorial_day(company, "Research & Development")

    # Step 6: Create Leave Applications
    print("\nStep 6: Creating Leave Applications...")
    leave_apps_result = create_leave_applications(company, leaves_path)  # <-- Capture the result
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Leave Management Configuration Complete!")
    print(f"{'='*60}\n")
    
    return {
        "leave_types": leave_types_result,
        "leave_period": leave_period_name,
        "leave_policy": policy_name,
        "compensatory_requests": comp_result,
        "leave_applications": leave_apps_result
    }

def leave_types_setup(leaves_path="employee_leaves.json"):
    """
    Configure all leave types for the company.
    This includes:
    1. Removing unwanted default leave types
    2. Configuring existing leave types
    3. Creating new leave types
    """
    # Sub-step 1: Remove unwanted default leave types
    print("\n  → Removing unwanted leave types...")
    removed_count, remove_errors  = remove_unwanted_leave_types(leaves_path)
    
    # Sub-step 2: Configure leave types
    print("\n  → Configuring leave types...")
    configured_count, config_errors = configure_leave_types(leaves_path)
    
    print("\n  ✓ Leave types setup complete")

    return {
        "removed": removed_count,
        "configured": configured_count,
        "errors": len(remove_errors) + len(config_errors)
    }

def remove_unwanted_leave_types(leaves_path="employee_leaves.json"):
    """
    Remove types from default list that we do not need.
    
    :param leave_types_to_remove: List of leave types to remove
    :return: tuple: (removed_count, errors_list)
    """
    removed_count = 0
    errors = []

    # Load data
    leave_types_to_remove =  load_data(leaves_path, key="leave_types_to_remove")

    for leave_type_name in leave_types_to_remove:
        try:
            if frappe.db.exists("Leave Type", leave_type_name):
                # Check if it's being used
                allocations = frappe.db.count("Leave Allocation", {"leave_type": leave_type_name})
                applications = frappe.db.count("Leave Application", {"leave_type": leave_type_name})
                
                if allocations > 0 or applications > 0:
                    print(f"  ⚠ Cannot remove '{leave_type_name}': In use ({allocations} allocations, {applications} applications)")
                    errors.append(f"{leave_type_name}: In use")
                else:
                    frappe.delete_doc("Leave Type", leave_type_name, force=True)
                    removed_count += 1
                    print(f"  ✓ Removed: {leave_type_name}")
            else:
                print(f"  ↻ Already removed: {leave_type_name}")
        except Exception as e:
            errors.append(f"{leave_type_name}: {str(e)[:50]}")
            print(f"  ⚠ Error removing {leave_type_name}: {str(e)[:50]}")
    
    print(f"\n  Summary: Removed {removed_count} leave types")
    if errors:
        print(f"  ⚠ {len(errors)} errors encountered")

    return removed_count, errors

def configure_leave_types(leaves_path="employee_leaves.json"):
    """
    Configure leave types with company policies:
    - Sick Leave
    - Compensatory Off
    - Leave Without Pay
    - Vacation Leave (new)
    
    Returns:
        tuple: (configured_count, errors_list)
    """
    results = []
    errors = []
    
    results.append(configure_sick_leave(leaves_path))
    results.append(configure_compensatory_off(leaves_path))
    results.append(configure_leave_without_pay(leaves_path))
    results.append(configure_vacation_leave(leaves_path))
    
    # Count successes (True values)
    configured_count = sum(1 for r in results if r)
    
    return configured_count, errors


def configure_sick_leave(leaves_path="employee_leaves.json"):
    """
    Configure Sick Leave:
    - Maximum Leave Allocation: 5 days per year
    - Allow After: 1 working day
    - Maximum Consecutive: 5 days
    - Carry Forward: Yes (up to 10 days, expires after 730 days/2 years)
    - Encashment: No
    """

    # Load data
    leaves_data = load_data(leaves_path, key="custom_leave_types")
    sick_leave_data = leaves_data["sick_leave"]
    leave_type_name = sick_leave_data["leave_type_name"]

    try:
        if frappe.db.exists("Leave Type", leave_type_name):
            leave_type = frappe.get_doc("Leave Type", leave_type_name)
            print(f"  ↻ Updating existing: {leave_type_name}")
        else:
            leave_type = frappe.get_doc({
                "doctype": "Leave Type",
                "leave_type_name": leave_type_name
            })
            print(f"  ✓ Creating: {leave_type_name}")
        
        # Set configuration
        leave_type.max_leaves_allowed = sick_leave_data["max_leaves_allowed"]
        leave_type.applicable_after =  sick_leave_data["applicable_after"]
        leave_type.max_continuous_days_allowed = sick_leave_data["max_continuous_days_allowed"]
        leave_type.is_carry_forward = sick_leave_data["is_carry_forward"]
        leave_type.maximum_carry_forwarded_leaves = sick_leave_data["maximum_carry_forwarded_leaves"]
        leave_type.expire_carry_forwarded_leaves_after_days = sick_leave_data["expire_carry_forwarded_leaves_after_days"]
        leave_type.allow_encashment = sick_leave_data["allow_encashment"]
        leave_type.is_lwp = sick_leave_data["is_lwp"]
        leave_type.is_compensatory = sick_leave_data["is_compensatory"]
        leave_type.include_holiday = sick_leave_data["include_holiday"]
        
        if leave_type.is_new():
            leave_type.insert(ignore_permissions=True)
        else:
            leave_type.save(ignore_permissions=True)
        
        print(f"    • Max allocation: 5 days/year")
        print(f"    • Carry forward: Up to 10 days (expires after 2 years)")
        print(f"    • Max consecutive: 5 days")
        return True
        
    except Exception as e:
        print(f"  ⚠ Error configuring {leave_type_name}: {str(e)[:80]}")
        return False


def configure_compensatory_off(leaves_path="employee_leaves.json"):
    """
    Configure Compensatory Off:
    - Maximum Leave Allocation: 0 (unlimited, earned by working extra)
    - Allow After: 0 working days
    - Maximum Consecutive: 2 days
    - Carry Forward: No
    - Encashment: No
    - Is Compensatory: Yes
    - NOT included in Leave Policy (earned dynamically)
    """
    # Load data
    leaves_data = load_data(leaves_path, key="custom_leave_types")
    comp_off_leave_data = leaves_data["compensatory_off"]
    leave_type_name = comp_off_leave_data["leave_type_name"]
    
    try:
        if frappe.db.exists("Leave Type", leave_type_name):
            leave_type = frappe.get_doc("Leave Type", leave_type_name)
            print(f"  ↻ Updating existing: {leave_type_name}")
        else:
            leave_type = frappe.get_doc({
                "doctype": "Leave Type",
                "leave_type_name": leave_type_name
            })
            print(f"  ✓ Creating: {leave_type_name}")
        
        # Set configuration
        leave_type.max_leaves_allowed = comp_off_leave_data["max_leaves_allowed"]  # 0 means unlimited
        leave_type.applicable_after = comp_off_leave_data["applicable_after"]
        leave_type.max_continuous_days_allowed = comp_off_leave_data["max_continuous_days_allowed"]
        leave_type.is_carry_forward = comp_off_leave_data["is_carry_forward"]
        leave_type.allow_encashment = comp_off_leave_data["allow_encashment"]
        leave_type.is_compensatory = comp_off_leave_data["is_compensatory"]  # YES - This IS compensatory leave
        leave_type.is_lwp = comp_off_leave_data["is_lwp"]
        leave_type.include_holiday = comp_off_leave_data["include_holiday"] # Don't include holidays in leave count
        leave_type.earning_component = comp_off_leave_data["earning_component"] # Clear earning component
        
        if leave_type.is_new():
            leave_type.insert(ignore_permissions=True)
        else:
            leave_type.save(ignore_permissions=True)
        
        print(f"    • Unlimited allocation (earned by working on holidays/weekends)")
        print(f"    • Max consecutive: 2 days")
        print(f"    • No carry forward or encashment")
        print(f"    • Not included in Leave Policy (earned dynamically)")
        return True

    except Exception as e:
        print(f"  ⚠ Error configuring {leave_type_name}: {str(e)[:80]}")
        return False

def configure_leave_without_pay(leaves_path="employee_leaves.json"):
    """
    Configure Leave Without Pay:
    - Maximum Leave Allocation: 0 (unlimited)
    - Allow After: 0 working days
    - Maximum Consecutive: 30 days
    - Carry Forward: No
    - Encashment: No
    - Is LWP: Yes
    - NOT included in Leave Policy (always available)
    """
    leave_type_name = "Leave Without Pay"

    # Load data
    leaves_data = load_data(leaves_path, key="custom_leave_types")
    lwp_leave_data = leaves_data["leave_without_pay"]
    leave_type_name = lwp_leave_data["leave_type_name"]
    
    try:
        if frappe.db.exists("Leave Type", leave_type_name):
            leave_type = frappe.get_doc("Leave Type", leave_type_name)
            print(f"  ↻ Updating existing: {leave_type_name}")
        else:
            leave_type = frappe.get_doc({
                "doctype": "Leave Type",
                "leave_type_name": leave_type_name
            })
            print(f"  ✓ Creating: {leave_type_name}")
        
        # Set configuration
        leave_type.max_leaves_allowed = lwp_leave_data["max_leaves_allowed"]
        leave_type.applicable_after = lwp_leave_data["applicable_after"]
        leave_type.max_continuous_days_allowed = lwp_leave_data["max_continuous_days_allowed"]
        leave_type.is_carry_forward = lwp_leave_data["is_carry_forward"]
        leave_type.allow_encashment = lwp_leave_data["allow_encashment"]
        leave_type.is_lwp = lwp_leave_data["is_lwp"] # Mark as Leave Without Pay
        leave_type.is_compensatory = lwp_leave_data["is_compensatory"]
        leave_type.include_holiday = lwp_leave_data["include_holiday"] # Don't include holidays in leave count
        leave_type.earning_component = lwp_leave_data["earning_component"] # Clear earning component
        
        if leave_type.is_new():
            leave_type.insert(ignore_permissions=True)
        else:
            leave_type.save(ignore_permissions=True)
        
        print(f"    • Unlimited allocation")
        print(f"    • Max consecutive: 30 days")
        print(f"    • Unpaid leave (reduces salary)")
        print(f"    • Not included in Leave Policy (always available)")
        return True

    except Exception as e:
        print(f"  ⚠ Error configuring {leave_type_name}: {str(e)[:80]}")
        return False


def configure_vacation_leave(leaves_path="employee_leaves.json"):
    """
    Configure Vacation Leave:
    - Maximum Leave Allocation: 15 days per year
    - Allow After: 90 working days (~3 months)
    - Maximum Consecutive: 15 days
    - Carry Forward: No
    - Encashment: Yes (up to 15 days, earning component: Vacation Encashment)
    - Non-Encashable: 0 days
    """
    # Load data
    leaves_data = load_data(leaves_path, key="custom_leave_types")
    vacation_leave_data = leaves_data["vacation_leave"]
    leave_type_name = vacation_leave_data["leave_type_name"]
    
    try:
        # First, ensure the Vacation Encashment salary component exists
        create_vacation_encashment_component()
        
        if frappe.db.exists("Leave Type", leave_type_name):
            leave_type = frappe.get_doc("Leave Type", leave_type_name)
            print(f"  ↻ Updating existing: {leave_type_name}")
        else:
            leave_type = frappe.get_doc({
                "doctype": "Leave Type",
                "leave_type_name": leave_type_name
            })
            print(f"  ✓ Creating: {leave_type_name}")
        
        # Set configuration
        leave_type.max_leaves_allowed = vacation_leave_data["max_leaves_allowed"]
        leave_type.applicable_after = vacation_leave_data["applicable_after"]
        leave_type.max_continuous_days_allowed = vacation_leave_data["max_continuous_days_allowed"]
        leave_type.is_carry_forward = vacation_leave_data["is_carry_forward"]
        leave_type.allow_encashment = vacation_leave_data["allow_encashment"]
        leave_type.max_encashable_leaves = vacation_leave_data["max_encashable_leaves"]
        leave_type.non_encashable_leaves = vacation_leave_data["non_encashable_leaves"]
        leave_type.earning_component = vacation_leave_data["earning_component"]
        leave_type.is_lwp = vacation_leave_data["is_lwp"]
        leave_type.is_compensatory = vacation_leave_data["is_compensatory"] # Not a compensatory leave
        leave_type.include_holiday = vacation_leave_data["include_holiday"] # Don't include holidays in leave count
        
        if leave_type.is_new():
            leave_type.insert(ignore_permissions=True)
        else:
            leave_type.save(ignore_permissions=True)
        
        print(f"    • Max allocation: 15 days/year")
        print(f"    • Available after: 90 working days")
        print(f"    • Encashment: Yes (up to 15 days)")
        print(f"    • Note: Encashment must be manually created by HR")
        return True

    except Exception as e:
        print(f"  ⚠ Error configuring {leave_type_name}: {str(e)[:80]}")
        return False


def create_vacation_encashment_component():
    """
    Create Vacation Encashment salary component if it doesn't exist
    """
    component_name = "Vacation Encashment"
    
    try:
        if not frappe.db.exists("Salary Component", component_name):
            salary_component = frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": component_name,
                "type": "Earning",
                "description": "Payment for unused vacation leave days"
            })
            salary_component.insert(ignore_permissions=True)
            print(f"  ✓ Created salary component: {component_name}")
        else:
            print(f"  ↻ Salary component exists: {component_name}")
    except Exception as e:
        print(f"  ⚠ Error creating salary component: {str(e)[:60]}")

def leave_period_setup(company="NovaSoft", leaves_path="employee_leaves.json"):
    """
    Configure leave period for the company.
    Creates a leave period for the full year 2025.
    """

    # Load data
    leave_period_data = load_data(leaves_path, key="leave_period")
    from_date = leave_period_data["from_date"]
    to_date = leave_period_data["to_date"]
    holiday_list = leave_period_data["holiday_list"]
    
    # Check if this leave period already exists
    existing_period = frappe.db.exists("Leave Period", {
        "company": company,
        "from_date": from_date,
        "to_date": to_date
    })
    
    try:
        if existing_period:
            leave_period = frappe.get_doc("Leave Period", existing_period)
            print(f"  ↻ Updating existing leave period: {leave_period.name}")
            
            # Update configuration
            leave_period.is_active = 1
            leave_period.optional_holiday_list = holiday_list
            leave_period.save(ignore_permissions=True)
        else:
            # Verify holiday list exists
            if not frappe.db.exists("Holiday List", holiday_list):
                print(f"  ⚠ Holiday List '{holiday_list}' not found, creating leave period without it")
                holiday_list = None
            
            # Create new leave period
            leave_period = frappe.get_doc({
                "doctype": "Leave Period",
                "from_date": from_date,
                "to_date": to_date,
                "is_active": 1,
                "company": company,
                "optional_holiday_list": holiday_list
            })
            leave_period.insert(ignore_permissions=True)
            print(f"  ✓ Created leave period: {leave_period.name}")
        
        print(f"    • Period: {from_date} to {to_date}")
        print(f"    • Company: {company}")
        print(f"    • Status: Active")
        if holiday_list:
            print(f"    • Holiday List: {holiday_list}")
        
        return leave_period.name
        
    except Exception as e:
        print(f"  ⚠ Error configuring leave period: {str(e)[:80]}")
        return None

def create_leave_policy(company="NovaSoft", leaves_path="employee_leaves.json"):
    """
    Create a standard leave policy for the company with the following allocations:
    - Sick Leave: 5 days
    - Vacation Leave: 15 days
    
    Note: Compensatory Off and Leave Without Pay are NOT included in the policy:
    - Compensatory Off: Earned dynamically by working on holidays/weekends
    - Leave Without Pay: Always available (unlimited)
    """
    # load data
    leave_policy_data = load_data(leaves_path, key="leave_policy")
    policy_name = f"{company} {leave_policy_data.get('title', 'Standard Leave Policy')}"
    sick_leave_allocation = leave_policy_data["sick_leave_allocation"]
    vacation_leave_allocation = leave_policy_data["vacation_leave_allocation"]
    
    try:
        # Check if policy already exists
        existing_policy = frappe.db.exists("Leave Policy", {"title": policy_name})
        
        if existing_policy:
            leave_policy = frappe.get_doc("Leave Policy", existing_policy)
            print(f"  ↻ Updating existing policy: {policy_name}")
            # If already submitted, we need to cancel and amend
            if leave_policy.docstatus == 1:
                print(f"  ⚠ Policy already submitted. Please manually update if needed.")
                return leave_policy.name
        else:
            leave_policy = frappe.get_doc({
                "doctype": "Leave Policy",
                "title": policy_name
            })
            print(f"  ✓ Creating policy: {policy_name}")
        
        # Clear existing details if updating
        leave_policy.leave_policy_details = []
        
        # Define leave allocations - ONLY types that need actual allocation
        leave_allocations = [
            {"leave_type": "Sick Leave", "annual_allocation": sick_leave_allocation},
            {"leave_type": "Vacation Leave", "annual_allocation": vacation_leave_allocation}
        ]
        
        # Add leave policy details
        for allocation in leave_allocations:
            # Verify leave type exists
            if frappe.db.exists("Leave Type", allocation["leave_type"]):
                leave_policy.append("leave_policy_details", {
                    "leave_type": allocation["leave_type"],
                    "annual_allocation": allocation["annual_allocation"]
                })
                print(f"    • {allocation['leave_type']}: {allocation['annual_allocation']} days")
            else:
                print(f"  ⚠ Leave Type '{allocation['leave_type']}' not found, skipping")
        
        if leave_policy.is_new():
            leave_policy.insert(ignore_permissions=True)
        else:
            leave_policy.save(ignore_permissions=True)
        
        # Submit the policy to make it active
        if leave_policy.docstatus == 0:
            leave_policy.submit()
            print(f"  ✓ Policy submitted and active")
        
        print(f"\n  Note: Compensatory Off and LWP not included in policy:")
        print(f"    • Compensatory Off: Earned by working extra (unlimited)")
        print(f"    • Leave Without Pay: Always available (unlimited)")
        
        return leave_policy.name
        
    except Exception as e:
        print(f"  ⚠ Error creating leave policy: {str(e)[:80]}")
        import traceback
        traceback.print_exc()
        return None

def assign_leave_policy_to_employees(company="NovaSoft", leave_period_name=None, leaves_path="employee_leaves.json"):
    """
    Assign the standard leave policy to all active employees in the company.
    This will automatically create leave allocations for Sick Leave and Vacation Leave.
    
    Compensatory Off and Leave Without Pay do not need allocation:
    - Compensatory Off: Earned dynamically
    - Leave Without Pay: Always available
    
    :param company: Company name
    :param leave_period_name: Leave Period name (e.g., "December 2025")
    """
    # load data
    leave_policy_data = load_data(leaves_path, key="leave_policy")
    title = leave_policy_data["title"]
    policy_title = f"{company} {title}"
    
    # Get the policy by title
    policy_name = frappe.db.get_value("Leave Policy", {"title": policy_title}, "name")
    
    if not policy_name:
        print(f"  ⚠ Leave Policy '{policy_title}' not found")
        return
    
    # Get all active employees for the company
    employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "status": "Active"
        },
        fields=["name", "employee_name"]
    )
    
    if not employees:
        print(f"  ⚠ No active employees found for company: {company}")
        return
    
    print(f"\n  Found {len(employees)} active employees")
    
    assigned_count = 0
    skipped_count = 0
    error_count = 0
    
    for emp in employees:
        try:
            # Check if employee already has an active policy assignment for this period
            existing_assignment = frappe.db.exists(
                "Leave Policy Assignment",
                {
                    "employee": emp.name,
                    "leave_policy": policy_name,
                    "docstatus": 1,
                    "leave_period": leave_period_name
                }
            )
            
            if existing_assignment:
                print(f"  ↻ Skipped {emp.employee_name}: Already has policy assigned")
                skipped_count += 1
                continue
            
            # Create leave policy assignment
            assignment = frappe.get_doc({
                "doctype": "Leave Policy Assignment",
                "employee": emp.name,
                "leave_policy": policy_name,
                "assignment_based_on": "Leave Period",
                "leave_period": leave_period_name,
                "carry_forward": 1  # Enable carry forward for eligible leave types
            })
            
            assignment.insert(ignore_permissions=True)
            assignment.submit()
            
            assigned_count += 1
            print(f"  ✓ Assigned to {emp.employee_name}")
            
        except Exception as e:
            error_count += 1
            print(f"  ⚠ Error assigning to {emp.employee_name}: {str(e)[:60]}")
    
    print(f"\n  Summary:")
    print(f"    • Assigned: {assigned_count}")
    print(f"    • Skipped: {skipped_count}")
    print(f"    • Errors: {error_count}")
    print(f"\n  Leave Allocations Created:")
    print(f"    • Sick Leave: 5 days per employee")
    print(f"    • Vacation Leave: 15 days per employee")
    print(f"\n  Available Without Allocation:")
    print(f"    • Compensatory Off: Earned by working extra")
    print(f"    • Leave Without Pay: Always available")


def create_compensatory_leave_requests_for_memorial_day(company="NovaSoft", department="Research & Development"):
    """
    Create Compensatory Leave Requests for employees in a specific department who worked on Memorial Day (2025-05-26).
    This follows the proper Frappe HR workflow:
    1. Verifies attendance exists for Memorial Day
    2. Creates Compensatory Leave Request
    3. System automatically creates Leave Allocation
    
    :param company: Company name
    :param department: Department name (without company abbreviation)
    
    Usage: 
        bench --site [sitename] execute hrms.demo_data.leaves_setup.create_compensatory_leave_requests_for_memorial_day
        
        Or with custom department:
        bench --site [sitename] execute hrms.demo_data.leaves_setup.create_compensatory_leave_requests_for_memorial_day --kwargs '{"company": "NovaSoft", "department": "Research & Development"}'
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Creating Compensatory Leave Requests for Memorial Day")
    print(f"Department: {department}")
    print(f"{'='*60}\n")
    
    memorial_day = "2025-05-26"
    
    # Get company abbreviation
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    if not company_abbr:
        print(f"  ⚠ Could not find company abbreviation for: {company}")
        return {"created": 0, "skipped": 0, "errors": 1}
    
    # Department format: "Department Name - ABBR"
    department_full_name = f"{department} - {company_abbr}"
    
    # Get all employees in the specified department
    employees = frappe.get_all(
        "Employee",
        filters={
            "company": company,
            "department": department_full_name,
            "status": "Active"
        },
        fields=["name", "employee_name"]
    )
    
    if not employees:
        print(f"  ⚠ No employees found for department: {department_full_name}")
        return {"created": 0, "skipped": 0, "errors": 0}
    
    print(f"Found {len(employees)} employees in {department}\n")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    errors = []
    
    for emp in employees:
        try:
            # Check if attendance exists for Memorial Day
            attendance = frappe.db.exists("Attendance", {
                "employee": emp.name,
                "attendance_date": memorial_day,
                "status": "Present",
                "docstatus": 1
            })
            
            if not attendance:
                print(f"  ⚠ {emp.employee_name}: No attendance found for Memorial Day")
                skipped_count += 1
                continue
            
            # Check if compensatory leave request already exists
            existing_request = frappe.db.exists("Compensatory Leave Request", {
                "employee": emp.name,
                "work_from_date": memorial_day,
                "work_end_date": memorial_day
            })
            
            if existing_request:
                print(f"  ↻ {emp.employee_name}: Request already exists")
                skipped_count += 1
                continue
            
            # Create Compensatory Leave Request
            comp_request = frappe.get_doc({
                "doctype": "Compensatory Leave Request",
                "employee": emp.name,
                "work_from_date": memorial_day,
                "work_end_date": memorial_day,
                "leave_type": "Compensatory Off",
                "reason": "Worked on Memorial Day holiday",
                "half_day": 0
            })
            
            comp_request.insert(ignore_permissions=True)
            comp_request.submit()
            
            created_count += 1
            print(f"  ✓ {emp.employee_name}: Created request (Allocation: {comp_request.leave_allocation})")
            
        except Exception as e:
            error_count += 1
            errors.append(f"{emp.employee_name}: {str(e)[:60]}")
            print(f"  ⚠ {emp.employee_name}: Error - {str(e)[:60]}")
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Compensatory Leave Request Creation Complete!")
    print(f"{'='*60}")
    print(f"\n  ✓ Created: {created_count} requests")
    print(f"  ↻ Skipped: {skipped_count}")
    print(f"  ⚠ Errors: {error_count}")
    
    if errors:
        print(f"\n  Errors encountered:")
        for err in errors[:10]:
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")
    
    print(f"\n{'='*60}\n")
    
    return {
        "created": created_count,
        "skipped": skipped_count,
        "errors": error_count
    }

def create_leave_applications(company="NovaSoft", leaves_path=None):
    """
    Create leave applications from the employee_leaves.json file.
    Applications can be in various statuses: Open, Approved, Rejected
    
    Usage: 
        bench --site [sitename] execute hrms.demo_data.leaves_setup.create_leave_applications
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"Creating Leave Applications for Company: {company}")
    print(f"{'='*60}\n")
    
    # Import load_data utility
    from hrms.demo_data.utils import load_data
    import os
    
    # Set default path if not provided
    if not leaves_path:
        leaves_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "employee_leaves.json"
        )
    
    # Load leave applications data using utility function
    applications_list = load_data(leaves_path, key="leave_applications")
    
    if not applications_list:
        print("  ⚠ No leave applications found in JSON file")
        return {"created": 0, "errors": 0}
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    errors = []
    
    for app_data in applications_list:
        emp_id = app_data.get("employee_id")
        emp_name = app_data.get("employee_name")
        leave_type = app_data.get("leave_type")
        from_date = app_data.get("from_date")
        to_date = app_data.get("to_date")
        status = app_data.get("status", "Open")
        
        try:
            # Verify employee exists
            if not frappe.db.exists("Employee", emp_id):
                print(f"  ⚠ {emp_name}: Employee not found ({emp_id})")
                skipped_count += 1
                continue
            
            # Check if leave application already exists
            existing_app = frappe.db.exists("Leave Application", {
                "employee": emp_id,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date
            })
            
            if existing_app:
                print(f"  ↻ {emp_name}: Application already exists ({leave_type}, {from_date})")
                skipped_count += 1
                continue
            
            # Get leave approver
            leave_approver_name = app_data.get("leave_approver")
            leave_approver = None
            if leave_approver_name:
                leave_approver = frappe.db.get_value(
                    "Employee",
                    {"employee_name": leave_approver_name},
                    "user_id"  # ✅ This returns email address
                )
            
            # Create leave application
            leave_app = frappe.get_doc({
                "doctype": "Leave Application",
                "employee": emp_id,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date,
                "half_day": app_data.get("half_day", 0),
                "half_day_date": app_data.get("half_day_date"),
                "description": app_data.get("description", ""),
                "leave_approver": leave_approver,
                "company": company
            })
            
            leave_app.insert(ignore_permissions=True)
            
            # Handle status transitions by directly updating DB (bypassing workflow)
            if status == "Approved":
                leave_app.docstatus = 1  # Mark as submitted
                leave_app.status = "Approved"
                leave_app.save(ignore_permissions=True)
                print(f"  ✓ {emp_name}: Created & Approved ({leave_type}, {from_date} to {to_date})")
            elif status == "Rejected":
                leave_app.docstatus = 1  # Mark as submitted
                leave_app.status = "Rejected"
                leave_app.save(ignore_permissions=True)
                print(f"  ✓ {emp_name}: Created & Rejected ({leave_type}, {from_date} to {to_date})")
            else:
                # Leave as draft (docstatus=0, status="Open")
                print(f"  ✓ {emp_name}: Created ({leave_type}, {from_date} to {to_date}) - Status: Open")

            created_count += 1
            
        except Exception as e:
            error_count += 1
            error_msg = f"{emp_name}: {str(e)[:60]}"
            errors.append(error_msg)
            print(f"  ⚠ {error_msg}")
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Leave Applications Creation Complete!")
    print(f"{'='*60}")
    print(f"\n  ✓ Created: {created_count}")
    print(f"  ↻ Skipped: {skipped_count}")
    print(f"  ⚠ Errors: {error_count}")
    
    if errors:
        print(f"\n  Errors encountered:")
        for err in errors[:10]:
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")
    
    print(f"\n{'='*60}\n")
    
    return {
        "created": created_count,
        "skipped": skipped_count,
        "errors": error_count
    }

# Utility functions to clear leave configuration (use with caution)
def clear_leave_configuration(company="NovaSoft", leaves_path="employee_leaves.json"):
    """
    Clear all leave configuration including policies, assignments, allocations, and leave types.
    Then restore default leave types.
    USE WITH CAUTION - This will delete all leave-related data!
    
    Usage: bench --site [sitename] execute hrms.demo_data.leaves_setup.clear_leave_configuration
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"⚠️  Clearing Leave Configuration")
    print(f"{'='*60}\n")
    
    errors = []
    
    # Step 1: Delete Leave Applications FIRST (they reference allocations)
    print("Step 1: Deleting Leave Applications...")
    delete_leave_applications(company, leaves_path)
    
    # Step 2: Delete Compensatory Leave Requests (they create allocations)
    print("\nStep 2: Deleting Compensatory Leave Requests...")
    clear_compensatory_leave_requests(company, errors)
    
    # Step 3: Delete Leave Allocations (created by assignments/requests)
    print("\nStep 3: Deleting Leave Allocations...")
    delete_leave_allocations(company, errors)
    
    # Step 4: Delete Leave Policy Assignments (they create allocations)
    print("\nStep 4: Deleting Leave Policy Assignments...")
    delete_leave_policy_assignments(company, errors)
    
    # Step 5: Delete Leave Policy
    print("\nStep 5: Deleting Leave Policy...")
    delete_leave_policy(company, errors)
    
    # Step 6: Delete Leave Period
    print("\nStep 6: Deleting Leave Period...")
    delete_leave_period(errors, company)
    
    # Step 7: Delete ALL Leave Types
    print("\nStep 7: Deleting ALL Leave Types...")
    deleted_count = delete_all_leave_types(errors)
    
    # Step 8: Delete Vacation Encashment Salary Component
    print("\nStep 8: Deleting Salary Components...")
    delete_vacation_encashment_component(errors)
    
    # Step 9: Restore Default Leave Types
    print("\nStep 9: Restoring Default Leave Types...")
    restore_default_leave_types(leaves_path)
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Leave Configuration Cleared and Defaults Restored!")
    print(f"{'='*60}")
    print(f"\n  ✓ Deleted {deleted_count} leave types")
    if errors:
        print(f"  ⚠ {len(errors)} errors encountered:")
        for err in errors[:10]:  # Show first 10
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")
    print(f"\n{'='*60}\n")
    
    return {
        "deleted_leave_types": deleted_count,
        "errors": len(errors)
    }

def delete_leave_policy_assignments(company, errors):
    """
    Cancel and delete all leave policy assignments for the company.
    Must be done before deleting leave allocations.
    """
    try:
        # Get all leave policy assignments for the company
        assignments = frappe.get_all(
            "Leave Policy Assignment",
            filters={"company": company},
            fields=["name", "docstatus", "employee"]
        )
        
        if not assignments:
            print(f"  ↻ No leave policy assignments found")
            return
        
        deleted_count = 0
        for assignment in assignments:
            try:
                doc = frappe.get_doc("Leave Policy Assignment", assignment.name)
                
                # Cancel if submitted
                if doc.docstatus == 1:
                    doc.cancel()
                    print(f"  ✓ Cancelled assignment: {assignment.employee}")
                
                # Delete
                frappe.delete_doc("Leave Policy Assignment", assignment.name, force=True)
                deleted_count += 1
                print(f"  ✓ Deleted assignment: {assignment.employee}")
                
            except Exception as e:
                errors.append(f"Assignment {assignment.name}: {str(e)[:50]}")
                print(f"  ⚠ Error deleting assignment {assignment.name}: {str(e)[:50]}")
        
        print(f"\n  Summary: Deleted {deleted_count} leave policy assignments")
        
    except Exception as e:
        errors.append(f"Leave Policy Assignments: {str(e)[:50]}")
        print(f"  ⚠ Error processing leave policy assignments: {str(e)[:50]}")


def delete_leave_allocations(company, errors):
    """
    Cancel and delete all leave allocations for the company.
    Must be done before deleting leave policy.
    """
    try:
        # Get all leave allocations for employees in the company
        allocations = frappe.get_all(
            "Leave Allocation",
            filters={"company": company},
            fields=["name", "docstatus", "employee", "leave_type"]
        )
        
        if not allocations:
            print(f"  ↻ No leave allocations found")
            return
        
        deleted_count = 0
        for allocation in allocations:
            try:
                doc = frappe.get_doc("Leave Allocation", allocation.name)
                
                # Cancel if submitted
                if doc.docstatus == 1:
                    doc.cancel()
                    print(f"  ✓ Cancelled allocation: {allocation.employee} - {allocation.leave_type}")
                
                # Delete
                frappe.delete_doc("Leave Allocation", allocation.name, force=True)
                deleted_count += 1
                print(f"  ✓ Deleted allocation: {allocation.employee} - {allocation.leave_type}")
                
            except Exception as e:
                errors.append(f"Allocation {allocation.name}: {str(e)[:50]}")
                print(f"  ⚠ Error deleting allocation {allocation.name}: {str(e)[:50]}")
        
        print(f"\n  Summary: Deleted {deleted_count} leave allocations")
        
    except Exception as e:
        errors.append(f"Leave Allocations: {str(e)[:50]}")
        print(f"  ⚠ Error processing leave allocations: {str(e)[:50]}")


def delete_leave_policy(company, errors):
    """
    Cancel and delete the leave policy for the company.
    Must be done after deleting leave allocations.
    """
    try:
        policy_title = f"{company} Standard Leave Policy"
        policy_name = frappe.db.get_value("Leave Policy", {"title": policy_title}, "name")
        
        if not policy_name:
            print(f"  ↻ Leave policy not found: {policy_title}")
            return
        
        doc = frappe.get_doc("Leave Policy", policy_name)
        
        # Cancel if submitted
        if doc.docstatus == 1:
            doc.cancel()
            print(f"  ✓ Cancelled policy: {policy_title}")
        
        # Delete
        frappe.delete_doc("Leave Policy", policy_name, force=True)
        print(f"  ✓ Deleted policy: {policy_title}")
        
    except Exception as e:
        errors.append(f"Leave Policy: {str(e)[:50]}")
        print(f"  ⚠ Error deleting leave policy: {str(e)[:50]}")

def delete_leave_period(errors, company="NovaSoft"):
    """
    Delete the leave period created by configure_leave_management
    """
    try:
        leave_period = frappe.db.exists("Leave Period", {
            "company": company,
            "from_date": "2025-01-01",
            "to_date": "2025-12-31"
        })
        if leave_period:
            # Check if it's being used
            allocations = frappe.db.count("Leave Allocation", {"leave_period": leave_period})
            policy_assignments = frappe.db.count("Leave Policy Assignment", {"leave_period": leave_period})
            
            if allocations > 0 or policy_assignments > 0:
                print(f"  ⚠ Cannot delete leave period: In use ({allocations} allocations, {policy_assignments} assignments)")
                errors.append(f"Leave Period: In use")
            else:
                frappe.delete_doc("Leave Period", leave_period, force=True)
                print(f"  ✓ Deleted leave period: {leave_period}")
        else:
            print(f"  ↻ Leave period not found or already deleted")
    except Exception as e:
        errors.append(f"Leave Period: {str(e)[:50]}")
        print(f"  ⚠ Error deleting leave period: {str(e)[:50]}")

def delete_all_leave_types(errors):
    """
    Delete all existing leave types in the system
    Returns the count of successfully deleted leave types
    """
    all_leave_types = frappe.get_all("Leave Type", pluck="name")
    deleted_count = 0
    
    for leave_type_name in all_leave_types:
        try:
            # Check if it's being used
            allocations = frappe.db.count("Leave Allocation", {"leave_type": leave_type_name})
            applications = frappe.db.count("Leave Application", {"leave_type": leave_type_name})
            
            if allocations > 0 or applications > 0:
                print(f"  ⚠ Cannot delete '{leave_type_name}': In use ({allocations} allocations, {applications} applications)")
                errors.append(f"{leave_type_name}: In use")
            else:
                frappe.delete_doc("Leave Type", leave_type_name, force=True)
                deleted_count += 1
                print(f"  ✓ Deleted: {leave_type_name}")
        except Exception as e:
            errors.append(f"{leave_type_name}: {str(e)[:50]}")
            print(f"  ⚠ Error deleting {leave_type_name}: {str(e)[:50]}")
    
    print(f"\n  Summary: Deleted {deleted_count} leave types")
    return deleted_count


def delete_vacation_encashment_component(errors):
    """
    Delete the Vacation Encashment salary component created for vacation leave encashment
    """
    try:
        if frappe.db.exists("Salary Component", "Vacation Encashment"):
            # Check if it's being used
            structures = frappe.db.count("Salary Detail", {"salary_component": "Vacation Encashment"})
            
            if structures > 0:
                print(f"  ⚠ Cannot delete 'Vacation Encashment': In use ({structures} salary structures)")
                errors.append(f"Vacation Encashment: In use")
            else:
                frappe.delete_doc("Salary Component", "Vacation Encashment", force=True)
                print(f"  ✓ Deleted salary component: Vacation Encashment")
        else:
            print(f"  ↻ Salary component 'Vacation Encashment' not found")
    except Exception as e:
        errors.append(f"Vacation Encashment: {str(e)[:50]}")
        print(f"  ⚠ Error deleting salary component: {str(e)[:50]}")

def clear_compensatory_leave_requests(company, errors):
    """
    Cancel and delete all compensatory leave requests for the company.
    Should be done before deleting leave allocations.
    """
    try:
        # Get all active employees in the company first
        employees = frappe.get_all(
            "Employee",
            filters={"company": company, "status": "Active"},
            pluck="name"
        )
        
        if not employees:
            print(f"  ↻ No employees found for company: {company}")
            return
        
        # Get all compensatory leave requests for these employees
        requests = frappe.get_all(
            "Compensatory Leave Request",
            filters={"employee": ["in", employees]},
            fields=["name", "docstatus", "employee", "work_from_date"]
        )
        
        if not requests:
            print(f"  ↻ No compensatory leave requests found")
            return
        
        deleted_count = 0
        for request in requests:
            try:
                doc = frappe.get_doc("Compensatory Leave Request", request.name)
                
                # Cancel if submitted
                if doc.docstatus == 1:
                    doc.cancel()
                    print(f"  ✓ Cancelled request: {request.employee} - {request.work_from_date}")
                
                # Delete
                frappe.delete_doc("Compensatory Leave Request", request.name, force=True)
                deleted_count += 1
                print(f"  ✓ Deleted request: {request.employee} - {request.work_from_date}")
                
            except Exception as e:
                errors.append(f"Comp Request {request.name}: {str(e)[:50]}")
                print(f"  ⚠ Error deleting request {request.name}: {str(e)[:50]}")
        
        print(f"\n  Summary: Deleted {deleted_count} compensatory leave requests")
        
    except Exception as e:
        errors.append(f"Compensatory Leave Requests: {str(e)[:80]}")
        print(f"  ⚠ Error processing compensatory leave requests: {str(e)[:80]}")

def restore_default_leave_types(leaves_path="employee_leaves.json"):
    """
    Restore the original default leave types with their default configurations
    """
    # Load data
    default_leave_types = load_data(leaves_path, key="default_leave_types")
    
    restored_count = 0
    for leave_type_name, config in default_leave_types.items():
        try:
            if not frappe.db.exists("Leave Type", leave_type_name):
                leave_type = frappe.get_doc({
                    "doctype": "Leave Type",
                    "leave_type_name": leave_type_name,
                    **config
                })
                leave_type.insert(ignore_permissions=True)
                restored_count += 1
                print(f"  ✓ Restored: {leave_type_name}")
            else:
                print(f"  ↻ Already exists: {leave_type_name}")
        except Exception as e:
            print(f"  ⚠ Error restoring {leave_type_name}: {str(e)[:60]}")
    
    print(f"\n  Summary: Restored {restored_count} default leave types")

def delete_leave_applications(company="NovaSoft", leaves_path=None):
    """
    Clear leave applications created from the employee_leaves.json file.
    USE WITH CAUTION - This will delete leave application data!
    
    Usage: 
        bench --site [sitename] execute hrms.demo_data.leaves_setup.clear_leave_applications
    """
    frappe.set_user("Administrator")
    
    print(f"\n{'='*60}")
    print(f"⚠️  Clearing Leave Applications for Company: {company}")
    print(f"{'='*60}\n")
    
    # Import load_data utility
    from hrms.demo_data.utils import load_data
    import os
    
    # Set default path if not provided
    if not leaves_path:
        leaves_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "employee_leaves.json"
        )
    
    # Load leave applications data using utility function
    applications_list = load_data(leaves_path, key="leave_applications")
    
    if not applications_list:
        print("  ⚠ No leave applications found in JSON file")
        return {"deleted": 0, "errors": 0}
    
    print("⚠️  Starting deletion process...\n")
    
    deleted_count = 0
    errors = []
    
    for app_data in applications_list:
        emp_id = app_data.get("employee_id")
        emp_name = app_data.get("employee_name")
        leave_type = app_data.get("leave_type")
        from_date = app_data.get("from_date")
        to_date = app_data.get("to_date")
        
        try:
            # Find matching leave application
            leave_apps = frappe.get_all("Leave Application", filters={
                "employee": emp_id,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date
            })
            
            for app in leave_apps:
                try:
                    doc = frappe.get_doc("Leave Application", app.name)
                    
                    # Cancel if submitted
                    if doc.docstatus == 1:
                        doc.cancel()
                        print(f"  ✓ Cancelled: {emp_name} - {leave_type} ({from_date})")
                    
                    # Delete
                    frappe.delete_doc("Leave Application", app.name, force=True)
                    deleted_count += 1
                    print(f"  ✓ Deleted: {emp_name} - {leave_type} ({from_date})")
                    
                except Exception as e:
                    errors.append(f"{emp_name} ({app.name}): {str(e)[:50]}")
                    print(f"  ⚠ Error deleting {app.name}: {str(e)[:50]}")
        
        except Exception as e:
            errors.append(f"{emp_name}: {str(e)[:50]}")
            print(f"  ⚠ Error processing {emp_name}: {str(e)[:50]}")
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print("✅ Leave Applications Deletion Complete!")
    print(f"{'='*60}")
    print(f"\n  ✓ Deleted: {deleted_count}")
    print(f"  ⚠ Errors: {len(errors)}")
    
    if errors:
        print(f"\n  Errors encountered:")
        for err in errors[:10]:
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")
    
    print(f"\n{'='*60}\n")
    
    return {
        "deleted": deleted_count,
        "errors": len(errors)
    }