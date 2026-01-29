"""
Payroll Setup - Demo Data Generator for HRMS
Creates Salary Components, Salary Structures, Structure Assignments, and Salary Slips

Design based on US tech company payroll with weekly schedules.

Salary Components:
- Base Salary (Salaried): For executives, NOT prorated by attendance
- Base Salary (Hourly): For staff, prorated by attendance
- House Rent Allowance: 40% of base for executives only
- 401K Contribution: 6% of base
- Health Insurance: Fixed per employee (Individual: $69.28/wk, Family: $150.12/wk)
- Income Tax Federal: Auto-calculated based on tax slabs
- Income Tax State: 5% California tax

Salary Structures:
- Salaried: For executives (C-Suite + General Counsel)
- Hourly: For all other staff

Author: shi-kejian
Version: 2.0.0

Usage:
    bench --site [sitename] execute hrms.demo_data.payroll_setup.create_payroll_data
"""

import frappe
from frappe.utils import getdate, nowdate, add_days, get_first_day, get_last_day
import json
import os

# Executive designations (Salaried structure)
EXECUTIVE_DESIGNATIONS = [
    'Chief Executive Officer (CEO)',
    'Chief Operating Officer (COO)',
    'Chief Technology Officer (CTO)',
    'Chief Financial Officer (CFO)',
    'Chief People Officer (CPO)',
    'Chief Revenue Officer (CRO)',
    'General Counsel (GC)'
]

# Salary components configuration
SALARY_COMPONENTS = [
    {
        "name": "Base Salary (Salaried)",
        "abbr": "BASE-SAL",
        "type": "Earning",
        "description": "Base salary for salaried employees - not affected by attendance",
        "is_tax_applicable": 1,
        "depends_on_payment_days": 0  # Executives - NO proration
    },
    {
        "name": "Base Salary (Hourly)",
        "abbr": "BASE-HR",
        "type": "Earning",
        "description": "Base salary for hourly employees - prorated by attendance",
        "is_tax_applicable": 1,
        "depends_on_payment_days": 1  # Staff - YES proration
    },
    {
        "name": "House Rent Allowance",
        "abbr": "HRA",
        "type": "Earning",
        "description": "Housing allowance for C-level executives (40% of base)",
        "is_tax_applicable": 1,
        "depends_on_payment_days": 0,  # NOT prorated for executives
        "amount_based_on_formula": 1,
        "formula": "base * 0.40"
    },
    {
        "name": "401K Contribution",
        "abbr": "401K",
        "type": "Deduction",
        "description": "Employee 401K retirement contribution (6% of base)",
        "is_tax_applicable": 0,  # Pre-tax deduction
        "depends_on_payment_days": 0,  # Fixed amount
        "amount_based_on_formula": 1,
        "formula": "base * 0.06"
    },
    {
        "name": "Health Insurance",
        "abbr": "HI",
        "type": "Deduction",
        "description": "Employee health insurance premium",
        "is_tax_applicable": 0,
        "depends_on_payment_days": 0  # Fixed amount
    },
    {
        "name": "Income Tax Federal",
        "abbr": "FIT",
        "type": "Deduction",
        "description": "Federal income tax withholding based on IRS tax slabs",
        "is_tax_applicable": 0,
        "depends_on_payment_days": 0,
        "is_income_tax_component": 1,
        "variable_based_on_taxable_salary": 1
    },
    {
        "name": "Income Tax State",
        "abbr": "SIT",
        "type": "Deduction",
        "description": "California state income tax (5% of taxable income)",
        "is_tax_applicable": 0,
        "depends_on_payment_days": 0,
        "amount_based_on_formula": 1,
        "formula": "gross_pay * 0.05"  # 5% of gross pay
    }
]


def ensure_fiscal_year(company):
    """Ensure Fiscal Year 2025 exists for the company"""
    fiscal_year = "2025"

    if not frappe.db.exists("Fiscal Year", fiscal_year):
        doc = frappe.get_doc({
            "doctype": "Fiscal Year",
            "year": fiscal_year,
            "year_start_date": "2025-01-01",
            "year_end_date": "2025-12-31",
            "is_short_year": 0
        })
        doc.append("companies", {"company": company})
        doc.insert(ignore_permissions=True)
        print(f"  Created Fiscal Year: {fiscal_year}")
    else:
        existing = frappe.get_doc("Fiscal Year", fiscal_year)
        company_exists = any(c.company == company for c in existing.companies)
        if not company_exists:
            existing.append("companies", {"company": company})
            existing.save(ignore_permissions=True)
            print(f"  Associated {company} with Fiscal Year {fiscal_year}")
        else:
            print(f"  Fiscal Year {fiscal_year} already exists for {company}")


def ensure_payroll_period(company):
    """Ensure Payroll Period exists for 2025 with tax slabs"""
    period_name = f"Payroll Period 2025 - {company}"

    if frappe.db.exists("Payroll Period", period_name):
        print(f"  Payroll Period already exists: {period_name}")
        return period_name

    # Create payroll period with federal tax slabs (2025 rates - simplified)
    doc = frappe.get_doc({
        "doctype": "Payroll Period",
        "name": period_name,
        "company": company,
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"
    })

    # Add federal tax slabs (simplified progressive rates for single filer)
    # These are approximate for demo purposes
    tax_slabs = [
        {"from_amount": 0, "to_amount": 11600, "percent_deduction": 10},
        {"from_amount": 11600, "to_amount": 47150, "percent_deduction": 12},
        {"from_amount": 47150, "to_amount": 100525, "percent_deduction": 22},
        {"from_amount": 100525, "to_amount": 191950, "percent_deduction": 24},
        {"from_amount": 191950, "to_amount": 243725, "percent_deduction": 32},
        {"from_amount": 243725, "to_amount": 609350, "percent_deduction": 35},
        {"from_amount": 609350, "to_amount": 0, "percent_deduction": 37},  # 0 = unlimited
    ]

    for slab in tax_slabs:
        doc.append("taxable_salary_slabs", slab)

    doc.insert(ignore_permissions=True)
    print(f"  Created Payroll Period: {period_name}")
    return period_name


def create_salary_components(counts):
    """Create salary components (earnings and deductions)"""
    for comp in SALARY_COMPONENTS:
        name = comp.get("name")

        if frappe.db.exists("Salary Component", name):
            print(f"  Already exists: {name}")
            continue

        try:
            doc_data = {
                "doctype": "Salary Component",
                "salary_component": name,
                "salary_component_abbr": comp.get("abbr"),
                "type": comp.get("type"),
                "description": comp.get("description", ""),
                "is_tax_applicable": comp.get("is_tax_applicable", 1),
                "depends_on_payment_days": comp.get("depends_on_payment_days", 1)
            }

            # Add formula-based fields if present
            if comp.get("amount_based_on_formula"):
                doc_data["amount_based_on_formula"] = 1
                doc_data["formula"] = comp.get("formula", "")

            # Add tax component fields if present
            if comp.get("is_income_tax_component"):
                doc_data["is_income_tax_component"] = 1
            if comp.get("variable_based_on_taxable_salary"):
                doc_data["variable_based_on_taxable_salary"] = 1

            doc = frappe.get_doc(doc_data)
            doc.insert(ignore_permissions=True)
            counts["salary_components"] += 1
            print(f"  Created: {name} ({comp.get('type')})")
        except Exception as e:
            counts["errors"].append(f"Component {name}: {str(e)[:80]}")
            print(f"  Error creating {name}: {str(e)[:80]}")


def create_salary_structures(company, counts):
    """Create Salaried and Hourly salary structures"""
    structures = [
        {
            "name": "Salaried",
            "description": "For executives (C-Suite and General Counsel)",
            "payroll_frequency": "Weekly",
            "earnings": [
                {"salary_component": "Base Salary (Salaried)"},
                {"salary_component": "House Rent Allowance"}
            ],
            "deductions": [
                {"salary_component": "401K Contribution"},
                {"salary_component": "Health Insurance"},
                {"salary_component": "Income Tax State"}
            ]
        },
        {
            "name": "Hourly",
            "description": "For all non-executive staff",
            "payroll_frequency": "Weekly",
            "earnings": [
                {"salary_component": "Base Salary (Hourly)"}
            ],
            "deductions": [
                {"salary_component": "401K Contribution"},
                {"salary_component": "Health Insurance"},
                {"salary_component": "Income Tax State"}
            ]
        }
    ]

    for struct in structures:
        name = struct.get("name")

        if frappe.db.exists("Salary Structure", name):
            print(f"  Already exists: {name}")
            continue

        try:
            doc = frappe.get_doc({
                "doctype": "Salary Structure",
                "name": name,
                "company": company,
                "is_active": "Yes",
                "payroll_frequency": struct.get("payroll_frequency", "Weekly"),
                "currency": frappe.db.get_value("Company", company, "default_currency") or "USD"
            })

            # Add earnings
            for earning in struct.get("earnings", []):
                doc.append("earnings", {
                    "salary_component": earning.get("salary_component"),
                    "amount_based_on_formula": 1 if earning.get("salary_component") == "House Rent Allowance" else 0
                })

            # Add deductions
            for deduction in struct.get("deductions", []):
                doc.append("deductions", {
                    "salary_component": deduction.get("salary_component"),
                    "amount_based_on_formula": 1 if deduction.get("salary_component") in ["401K Contribution", "Income Tax State"] else 0
                })

            doc.insert(ignore_permissions=True)
            doc.submit()
            counts["salary_structures"] += 1
            print(f"  Created: {name} ({struct.get('payroll_frequency')})")
        except Exception as e:
            counts["errors"].append(f"Structure {name}: {str(e)[:80]}")
            print(f"  Error creating {name}: {str(e)[:80]}")


def get_employees_by_criteria(company, include_executives=True, department=None):
    """Get employees based on criteria"""
    filters = {"company": company, "status": "Active"}

    employees = frappe.get_all(
        "Employee",
        filters=filters,
        fields=["name", "employee_name", "designation", "department", "date_of_joining"]
    )

    result = []
    for emp in employees:
        is_executive = emp.designation in EXECUTIVE_DESIGNATIONS

        # Filter based on criteria
        if include_executives and is_executive:
            result.append(emp)
        elif department and emp.department and department in emp.department:
            result.append(emp)

    return result


def load_employee_salaries():
    """Load annual salaries from employees_roster.json"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    roster_path = os.path.join(current_dir, "employees_roster.json")

    with open(roster_path, 'r') as f:
        data = json.load(f)

    # Create lookup by name
    salary_lookup = {}
    for emp in data.get("employees", []):
        name = f"{emp['first_name']} {emp.get('middle_name', '')} {emp['last_name']}".replace('  ', ' ').strip()
        salary_lookup[name] = emp.get("annual_salary", 75000)

    return salary_lookup


def create_structure_assignments(company, counts):
    """Assign salary structures to executives and Accounts department employees"""
    salary_lookup = load_employee_salaries()

    # Get executives
    executives = get_employees_by_criteria(company, include_executives=True, department=None)

    # Get Accounts department employees (includes non-executive staff)
    accounts_employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "designation", "department", "date_of_joining"]
    )
    accounts_employees = [e for e in accounts_employees if e.department and "Accounts" in e.department]

    # Combine and deduplicate
    all_employees = {e.name: e for e in executives}
    for e in accounts_employees:
        all_employees[e.name] = e

    for emp_id, emp in all_employees.items():
        is_executive = emp.designation in EXECUTIVE_DESIGNATIONS
        structure = "Salaried" if is_executive else "Hourly"

        # Get annual salary
        annual_salary = salary_lookup.get(emp.employee_name, 75000)

        # Weekly base = annual / 52
        weekly_base = round(annual_salary / 52, 2)

        # Check if assignment already exists
        existing = frappe.db.exists("Salary Structure Assignment", {
            "employee": emp_id,
            "salary_structure": structure
        })

        if existing:
            print(f"  Already assigned: {emp.employee_name} -> {structure}")
            continue

        try:
            # Health insurance: Individual $69.28/wk, Family $150.12/wk
            # For demo, assign family plan to executives, individual to staff
            health_insurance = 150.12 if is_executive else 69.28

            doc = frappe.get_doc({
                "doctype": "Salary Structure Assignment",
                "employee": emp_id,
                "salary_structure": structure,
                "from_date": emp.date_of_joining or "2025-01-01",
                "company": company,
                "base": weekly_base
            })
            doc.insert(ignore_permissions=True)
            doc.submit()
            counts["structure_assignments"] += 1
            print(f"  Assigned: {emp.employee_name} -> {structure} (Base: ${weekly_base:.2f}/wk, Annual: ${annual_salary:,})")
        except Exception as e:
            counts["errors"].append(f"Assignment {emp.employee_name}: {str(e)[:80]}")
            print(f"  Error assigning {emp.employee_name}: {str(e)[:80]}")


def create_salary_slips(company, counts, week_start="2025-11-17", week_end="2025-11-23"):
    """Create weekly salary slips for November 2025 (week of Nov 17-23)"""
    posting_date = week_end

    print(f"\n  Payroll Period: {week_start} to {week_end} (Weekly)")

    # Get all employees with structure assignments
    assignments = frappe.get_all(
        "Salary Structure Assignment",
        filters={"company": company, "docstatus": 1},
        fields=["employee", "salary_structure", "base"]
    )

    for assign in assignments:
        emp_id = assign.employee
        structure = assign.salary_structure

        # Get employee details
        emp = frappe.get_doc("Employee", emp_id)

        # Check if salary slip already exists for this period
        existing = frappe.db.exists("Salary Slip", {
            "employee": emp_id,
            "start_date": week_start,
            "end_date": week_end
        })

        if existing:
            print(f"  Salary slip exists: {emp.employee_name} ({week_start})")
            continue

        try:
            doc = frappe.get_doc({
                "doctype": "Salary Slip",
                "employee": emp_id,
                "salary_structure": structure,
                "company": company,
                "posting_date": posting_date,
                "start_date": week_start,
                "end_date": week_end,
                "payroll_frequency": "Weekly"
            })

            doc.insert(ignore_permissions=True)
            doc.reload()

            counts["salary_slips"] += 1
            print(f"  Created slip: {emp.employee_name}")
            print(f"    Gross: ${doc.gross_pay or 0:.2f}, Deductions: ${doc.total_deduction or 0:.2f}, Net: ${doc.net_pay or 0:.2f}")

        except Exception as e:
            counts["errors"].append(f"Salary slip {emp.employee_name}: {str(e)[:100]}")
            print(f"  Error creating slip for {emp.employee_name}: {str(e)[:100]}")


def create_payroll_data(company="NovaSoft"):
    """
    Create Payroll demo data

    :param company: Company name for payroll records
    """
    frappe.set_user("Administrator")

    print(f"\n{'='*60}")
    print(f"Creating Payroll Data for Company: {company}")
    print(f"Weekly payroll with US tax structure")
    print(f"{'='*60}\n")

    counts = {
        "salary_components": 0,
        "salary_structures": 0,
        "structure_assignments": 0,
        "salary_slips": 0,
        "errors": []
    }

    # Step 0: Ensure prerequisites
    print("\n" + "="*50)
    print("Step 0: Ensuring prerequisites...")
    print("="*50)
    ensure_fiscal_year(company)
    ensure_payroll_period(company)
    frappe.db.commit()

    # Step 1: Create Salary Components
    print("\n" + "="*50)
    print("Step 1: Creating Salary Components...")
    print("="*50)
    create_salary_components(counts)
    frappe.db.commit()

    # Step 2: Create Salary Structures
    print("\n" + "="*50)
    print("Step 2: Creating Salary Structures...")
    print("="*50)
    create_salary_structures(company, counts)
    frappe.db.commit()

    # Step 3: Assign Salary Structures
    print("\n" + "="*50)
    print("Step 3: Assigning Salary Structures...")
    print("="*50)
    create_structure_assignments(company, counts)
    frappe.db.commit()

    # Step 4: Create Salary Slips (Week of Nov 17-23, 2025)
    print("\n" + "="*50)
    print("Step 4: Creating Salary Slips (Week of Nov 17-23, 2025)...")
    print("="*50)
    create_salary_slips(company, counts)
    frappe.db.commit()

    # Print summary
    print(f"\n{'='*60}")
    print("Payroll Data Creation Complete!")
    print(f"{'='*60}")
    print(f"\n  Salary Components: {counts['salary_components']}")
    print(f"  Salary Structures: {counts['salary_structures']}")
    print(f"  Structure Assignments: {counts['structure_assignments']}")
    print(f"  Salary Slips: {counts['salary_slips']}")

    if counts["errors"]:
        print(f"\n  Errors: {len(counts['errors'])}")
        for err in counts["errors"][:10]:
            print(f"    - {err}")

    print(f"\n{'='*60}\n")

    return counts


def clear_payroll_data(company="NovaSoft"):
    """
    Clear existing payroll data
    USE WITH CAUTION - This will delete data!

    Usage: bench --site [sitename] execute hrms.demo_data.payroll_setup.clear_payroll_data
    """
    frappe.set_user("Administrator")

    print(f"\n{'='*60}")
    print(f"Clearing Payroll Data for Company: {company}")
    print(f"{'='*60}\n")

    deleted = {"slips": 0, "assignments": 0, "structures": 0, "components": 0}

    # Delete salary slips
    print("Deleting Salary Slips...")
    slips = frappe.get_all("Salary Slip", filters={"company": company})
    for slip in slips:
        try:
            doc = frappe.get_doc("Salary Slip", slip.name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Salary Slip", slip.name, force=True)
            deleted["slips"] += 1
        except Exception as e:
            print(f"  Error deleting slip {slip.name}: {str(e)[:50]}")

    # Delete structure assignments
    print("Deleting Structure Assignments...")
    assignments = frappe.get_all("Salary Structure Assignment", filters={"company": company})
    for a in assignments:
        try:
            doc = frappe.get_doc("Salary Structure Assignment", a.name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Salary Structure Assignment", a.name, force=True)
            deleted["assignments"] += 1
        except Exception as e:
            print(f"  Error deleting assignment {a.name}: {str(e)[:50]}")

    # Delete salary structures
    print("Deleting Salary Structures...")
    for name in ["Salaried", "Hourly"]:
        if frappe.db.exists("Salary Structure", name):
            try:
                doc = frappe.get_doc("Salary Structure", name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("Salary Structure", name, force=True)
                deleted["structures"] += 1
            except Exception as e:
                print(f"  Error deleting structure {name}: {str(e)[:50]}")

    # Delete custom salary components
    print("Deleting Custom Salary Components...")
    for comp in SALARY_COMPONENTS:
        name = comp.get("name")
        if frappe.db.exists("Salary Component", name):
            try:
                frappe.delete_doc("Salary Component", name, force=True)
                deleted["components"] += 1
            except Exception as e:
                print(f"  Error deleting component {name}: {str(e)[:50]}")

    frappe.db.commit()

    print(f"\n{'='*60}")
    print("Payroll Data Deletion Complete!")
    print(f"{'='*60}")
    print(f"  Deleted {deleted['slips']} Salary Slips")
    print(f"  Deleted {deleted['assignments']} Structure Assignments")
    print(f"  Deleted {deleted['structures']} Salary Structures")
    print(f"  Deleted {deleted['components']} Salary Components")
    print(f"{'='*60}\n")

    return deleted
