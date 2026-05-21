"""
Demo data setup script for Realtyna HRMS
Run with: bench --site hr.localhost execute hrms.demo_setup.execute
"""

import frappe
from frappe.utils import today, add_months, getdate, nowdate
import datetime



def execute():
    frappe.set_user("Administrator")

    print("\n=== Starting Demo Setup ===\n")

    # 1. Create Leave Types
    create_leave_types()

    # 2. Create HR Manager user + employee
    create_hr_manager()

    # 3. Create HR Employee user + employee
    create_hr_employee()

    # 4. Create Salary Slip for Chandler
    create_salary_slip_for_chandler()

    frappe.db.commit()
    print("\n=== Demo Setup Complete ===\n")


def create_leave_types():
    print("Creating Leave Types...")

    leave_types = [
        {
            "name": "Annual Leave",
            "max_leaves_allowed": 20,
            "allow_encashment": 1,
            "is_carry_forward": 1,
            "max_carry_forwarded_leaves": 10,
            "description": "Annual paid leave entitlement for all employees.",
        },
        {
            "name": "Sick Leave",
            "max_leaves_allowed": 12,
            "allow_encashment": 0,
            "is_carry_forward": 0,
            "description": "Leave for medical illness or injury.",
        },
        {
            "name": "Casual Leave",
            "max_leaves_allowed": 10,
            "allow_encashment": 0,
            "is_carry_forward": 0,
            "description": "Short leave for personal or family matters.",
        },
        {
            "name": "Maternity Leave",
            "max_leaves_allowed": 90,
            "allow_encashment": 0,
            "is_carry_forward": 0,
            "description": "Leave for expecting mothers before and after childbirth.",
        },
        {
            "name": "Paternity Leave",
            "max_leaves_allowed": 10,
            "allow_encashment": 0,
            "is_carry_forward": 0,
            "description": "Leave for new fathers after the birth of a child.",
        },
        {
            "name": "Bereavement Leave",
            "max_leaves_allowed": 5,
            "allow_encashment": 0,
            "is_carry_forward": 0,
            "description": "Leave granted for the death of an immediate family member.",
        },
        {
            "name": "Unpaid Leave",
            "max_leaves_allowed": 0,
            "allow_encashment": 0,
            "is_carry_forward": 0,
            "is_lwp": 1,
            "description": "Leave without pay — approved by manager.",
        },
        {
            "name": "Study Leave",
            "max_leaves_allowed": 5,
            "allow_encashment": 0,
            "is_carry_forward": 0,
            "description": "Leave for examinations or professional development courses.",
        },
    ]

    for lt in leave_types:
        if frappe.db.exists("Leave Type", lt["name"]):
            print(f"  [SKIP] Leave Type '{lt['name']}' already exists")
            continue

        doc = frappe.new_doc("Leave Type")
        doc.leave_type_name = lt["name"]
        doc.max_leaves_allowed = lt.get("max_leaves_allowed", 0)
        doc.allow_encashment = lt.get("allow_encashment", 0)
        doc.is_carry_forward = lt.get("is_carry_forward", 0)
        doc.max_carry_forwarded_leaves = lt.get("max_carry_forwarded_leaves", 0)
        doc.is_lwp = lt.get("is_lwp", 0)
        doc.description = lt.get("description", "")
        doc.insert(ignore_permissions=True)
        print(f"  [OK] Created Leave Type: {lt['name']}")


def create_user(email, first_name, last_name, roles, send_welcome=False):
    """Create or update a Frappe user with given roles."""
    full_name = f"{first_name} {last_name}"

    if frappe.db.exists("User", email):
        print(f"  [SKIP] User '{email}' already exists — updating roles")
        user = frappe.get_doc("User", email)
    else:
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.full_name = full_name
        user.send_welcome_email = 0
        user.new_password = "Realtyna@2024!"

    # Clear existing roles and set fresh
    user.roles = []
    for role in roles:
        user.append("roles", {"role": role})

    user.save(ignore_permissions=True)
    print(f"  [OK] User '{email}' saved with roles: {roles}")
    return user


def ensure_designation(designation):
    """Create designation if it doesn't exist."""
    if designation and not frappe.db.exists("Designation", designation):
        d = frappe.new_doc("Designation")
        d.designation_name = designation
        d.insert(ignore_permissions=True)
        print(f"  [OK] Created Designation: {designation}")


def next_employee_number():
    """Generate next EMP-XXX number."""
    last = frappe.db.sql(
        "SELECT employee_number FROM tabEmployee WHERE employee_number LIKE 'EMP-%' ORDER BY employee_number DESC LIMIT 1"
    )
    if last and last[0][0]:
        num = int(last[0][0].replace("EMP-", "")) + 1
    else:
        num = 1
    return f"EMP-{num:03d}"


def create_employee_for_user(
    user_email,
    first_name,
    last_name,
    designation,
    department,
    gender="Male",
    date_of_birth="1990-01-01",
    company="Realtyna",
    date_of_joining=None,
):
    """Create an Employee linked to a Frappe user."""
    full_name = f"{first_name} {last_name}"
    ensure_designation(designation)

    # Check if employee already linked to this user
    existing = frappe.db.get_value("Employee", {"user_id": user_email}, "name")
    if existing:
        print(f"  [SKIP] Employee for '{user_email}' already exists: {existing}")
        return frappe.get_doc("Employee", existing)

    if not date_of_joining:
        date_of_joining = today()

    # Resolve department — Frappe stores departments as "Name - AbbrevCompany"
    # First try direct name match, then search by department_name field
    dept_doc_name = None
    if department:
        # Try direct name (e.g. "Human Resources - R")
        abbrev = frappe.db.get_value("Company", company, "abbr") or ""
        candidate = f"{department} - {abbrev}" if abbrev else department
        if frappe.db.exists("Department", candidate):
            dept_doc_name = candidate
        else:
            # Search by department_name field
            found = frappe.db.get_value("Department", {"department_name": department, "company": company}, "name")
            if found:
                dept_doc_name = found
            else:
                # Create new department
                dept = frappe.new_doc("Department")
                dept.department_name = department
                dept.company = company
                dept.insert(ignore_permissions=True)
                dept_doc_name = dept.name
                print(f"  [OK] Created Department: {dept.name}")

    emp = frappe.new_doc("Employee")
    emp.employee_name = full_name
    emp.first_name = first_name
    emp.last_name = last_name
    emp.employee_number = next_employee_number()
    emp.gender = gender
    emp.date_of_birth = date_of_birth
    emp.user_id = user_email
    emp.company = company
    emp.designation = designation
    if dept_doc_name:
        emp.department = dept_doc_name
    emp.date_of_joining = date_of_joining
    emp.status = "Active"
    emp.insert(ignore_permissions=True)
    print(f"  [OK] Employee '{full_name}' created: {emp.name} ({emp.employee_number})")
    return emp


def create_hr_manager():
    print("\nCreating HR Manager...")
    email = "sarah.johnson@realtyna.net"
    roles = ["HR Manager", "HR User", "Leave Approver", "Expense Approver", "Employee"]
    create_user(email, "Sarah", "Johnson", roles)
    create_employee_for_user(
        email,
        "Sarah",
        "Johnson",
        designation="HR Manager",
        department="Human Resources",
        gender="Female",
        date_of_birth="1988-04-22",
        date_of_joining="2023-01-15",
    )


def create_hr_employee():
    print("\nCreating HR Employee...")
    email = "james.wilson@realtyna.net"
    roles = ["Employee"]
    create_user(email, "James", "Wilson", roles)
    create_employee_for_user(
        email,
        "James",
        "Wilson",
        designation="Software Developer",
        department="Engineering",
        gender="Male",
        date_of_birth="1995-09-10",
        date_of_joining="2024-03-01",
    )


def ensure_holiday_list():
    """Create a Holiday List Assignment for Chandler so salary slips can be generated.

    HRMS v16 uses the Holiday List Assignment doctype (not company.default_holiday_list).
    An assignment must be submitted and linked to either employee or company.
    The assignment from_date must be within the holiday list's date range.
    """
    # Find the best holiday list available
    results = frappe.db.sql(
        "SELECT name, from_date, to_date FROM `tabHoliday List` ORDER BY from_date DESC LIMIT 1",
        as_dict=True,
    )
    if not results:
        print("  [WARN] No Holiday List exists — creating a basic one")
        results = [_create_basic_holiday_list()]

    holiday_list_name = results[0]["name"]
    # Assignment from_date must be within the holiday list dates
    hl_from_date = str(results[0]["from_date"])

    # Create Holiday List Assignment for Chandler (employee)
    _ensure_hla("Employee", "Chandler P", holiday_list_name, hl_from_date)

    # Also create one for the company so all employees benefit
    _ensure_hla("Company", "Realtyna", holiday_list_name, hl_from_date)


def _ensure_hla(applicable_for, assigned_to, holiday_list, from_date):
    """Create + submit a Holiday List Assignment if one doesn't exist."""
    existing = frappe.db.sql(
        """SELECT name FROM `tabHoliday List Assignment`
           WHERE assigned_to=%s AND holiday_list=%s AND docstatus=1 LIMIT 1""",
        (assigned_to, holiday_list),
        as_dict=True,
    )
    if existing:
        print(f"  [SKIP] Holiday List Assignment already exists for {assigned_to}")
        return

    hla = frappe.new_doc("Holiday List Assignment")
    hla.applicable_for = applicable_for
    hla.assigned_to = assigned_to
    hla.holiday_list = holiday_list
    hla.from_date = from_date
    hla.insert(ignore_permissions=True)
    hla.submit()
    frappe.db.commit()
    print(f"  [OK] Created Holiday List Assignment for {assigned_to} ({applicable_for}) → {holiday_list}")


def _create_basic_holiday_list():
    """Create a minimal 2025-2026 holiday list for Realtyna."""
    hl = frappe.new_doc("Holiday List")
    hl.holiday_list_name = "Realtyna 2026"
    hl.from_date = "2024-01-01"
    hl.to_date = "2026-12-31"
    holidays = [
        ("2026-01-01", "New Year's Day"),
        ("2026-07-04", "Independence Day"),
        ("2026-12-25", "Christmas Day"),
    ]
    for d, desc in holidays:
        hl.append("holidays", {"holiday_date": d, "description": desc})
    hl.insert(ignore_permissions=True)
    print(f"  [OK] Created Holiday List: {hl.name}")
    return {"name": hl.name}


def ensure_salary_component(name, abbr, component_type):
    """Create salary component if it doesn't exist."""
    if not frappe.db.exists("Salary Component", name):
        sc = frappe.new_doc("Salary Component")
        sc.salary_component = name
        sc.salary_component_abbr = abbr
        sc.type = component_type
        sc.insert(ignore_permissions=True)
        print(f"  [OK] Created Salary Component: {name} ({component_type})")


def enrich_salary_structure(structure_name):
    """Ensure salary components exist (structure rows already added via SQL patch)."""
    components_to_create = [
        ("House Rent Allowance", "HRA", "Earning"),
        ("Transport Allowance", "TA", "Earning"),
        ("Professional Tax", "PT", "Deduction"),
        ("Provident Fund", "PF", "Deduction"),
    ]
    for name, abbr, ctype in components_to_create:
        ensure_salary_component(name, abbr, ctype)

    # Count rows to verify
    count = frappe.db.sql(
        "SELECT COUNT(*) as cnt FROM `tabSalary Detail` WHERE parent=%s", structure_name, as_dict=True
    )
    print(f"  [INFO] Salary Structure has {count[0]['cnt']} components")


def create_salary_slip_for_chandler():
    print("\nCreating Salary Slip for Chandler...")

    employee_name = "Chandler P"

    # Verify employee exists
    if not frappe.db.exists("Employee", employee_name):
        print(f"  [ERROR] Employee '{employee_name}' not found!")
        return

    # Ensure company has a holiday list
    ensure_holiday_list()

    # For demo purposes, set joining date to 2024-01-01 so slips can be created
    emp = frappe.get_doc("Employee", employee_name)
    changed = False
    if str(emp.date_of_joining) > "2024-01-01":
        emp.date_of_joining = "2024-01-01"
        changed = True
    # Ensure holiday list is set on the employee directly
    if not emp.holiday_list:
        hl = frappe.db.sql("SELECT name FROM `tabHoliday List` ORDER BY from_date DESC LIMIT 1", as_dict=True)
        if hl:
            emp.holiday_list = hl[0]["name"]
            changed = True
            print(f"  [OK] Set holiday list '{emp.holiday_list}' on Chandler employee record")
    if changed:
        emp.save(ignore_permissions=True)
        frappe.db.commit()
        if str(emp.date_of_joining) <= "2024-01-01":
            print(f"  [OK] Updated Chandler's joining date to 2024-01-01 (demo)")

    # Ensure salary structure assignment exists
    structure_name = "Backend Developer Structure"
    if not frappe.db.exists("Salary Structure", structure_name):
        print(f"  [ERROR] Salary Structure '{structure_name}' not found!")
        return

    # Enrich salary structure with realistic components
    enrich_salary_structure(structure_name)

    # Clear Frappe doc cache so get_cached_doc picks up SQL-inserted salary components
    frappe.clear_cache()

    # Create Salary Structure Assignment if not exists
    assignment_exists = frappe.db.exists(
        "Salary Structure Assignment",
        {"employee": employee_name, "salary_structure": structure_name},
    )
    if not assignment_exists:
        assignment = frappe.new_doc("Salary Structure Assignment")
        assignment.employee = employee_name
        assignment.salary_structure = structure_name
        assignment.from_date = "2024-01-01"
        assignment.base = 8500
        assignment.company = "Realtyna"
        assignment.insert(ignore_permissions=True)
        assignment.submit()
        print(f"  [OK] Salary Structure assigned to {employee_name}")
    else:
        print(f"  [SKIP] Salary Structure already assigned to {employee_name}")

    # Create salary slips for the last 3 months (nice demo view)
    today_date = getdate(today())

    slips_created = 0
    for months_back in range(1, 4):
        # Calculate month boundaries
        target = today_date.replace(day=1)
        for _ in range(months_back):
            target = (target - datetime.timedelta(days=1)).replace(day=1)
        start_date = target
        # Last day of that month
        if target.month == 12:
            end_date = target.replace(year=target.year + 1, month=1, day=1) - datetime.timedelta(days=1)
        else:
            end_date = target.replace(month=target.month + 1, day=1) - datetime.timedelta(days=1)

        month_str = start_date.strftime("%B %Y")

        # Check if slip already exists for this period
        existing_slip = frappe.db.exists(
            "Salary Slip",
            {
                "employee": employee_name,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        if existing_slip:
            print(f"  [SKIP] Salary Slip for {month_str} already exists")
            continue

        try:
            slip = frappe.new_doc("Salary Slip")
            slip.employee = employee_name
            # Fix naming: default_series is set in __init__ before employee is assigned
            slip.default_series = f"Sal Slip/{employee_name}/.#####"
            slip.salary_structure = structure_name
            slip.start_date = start_date
            slip.end_date = end_date
            slip.company = "Realtyna"
            slip.posting_date = end_date

            slip.insert(ignore_permissions=True)
            slip.get_emp_and_working_day_details()
            slip.save(ignore_permissions=True)
            slip.submit()

            slips_created += 1
            print(f"  [OK] Salary Slip for {month_str}: {slip.name}")
            print(f"       Gross: {slip.gross_pay}  |  Net: {slip.net_pay}")
        except Exception as e:
            print(f"  [WARN] Could not create slip for {month_str}: {e}")

    if slips_created == 0:
        print("  [INFO] All salary slips already exist.")
