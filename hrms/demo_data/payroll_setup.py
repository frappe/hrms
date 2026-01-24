"""
Payroll Setup - Demo Data Generator for HRMS
Creates Salary Components, Salary Structures, Structure Assignments, and Salary Slips

Author: shi-kejian
Version: 1.0.0

Usage:
    bench --site [sitename] execute hrms.demo_data.payroll_setup.create_payroll_data
    Or with custom JSON path:
    bench --site [sitename] execute hrms.demo_data.payroll_setup.create_payroll_data --kwargs '{"payroll_path": "/path/to/file.json"}'
"""

import frappe
from frappe.utils import getdate, nowdate, add_days, get_first_day, get_last_day
from hrms.demo_data.utils import load_data


def ensure_fiscal_year(company):
    """Ensure Fiscal Year 2025 exists for the company (required for salary slips)"""
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
        # Check if company is associated
        existing = frappe.get_doc("Fiscal Year", fiscal_year)
        company_exists = any(c.company == company for c in existing.companies)
        if not company_exists:
            existing.append("companies", {"company": company})
            existing.save(ignore_permissions=True)
            print(f"  Associated {company} with Fiscal Year {fiscal_year}")
        else:
            print(f"  Fiscal Year {fiscal_year} already exists for {company}")


def create_payroll_data(company="NovaSoft", payroll_path=None):
    """
    Create Payroll demo data from JSON file

    :param company: Company name for payroll records
    :param payroll_path: Path to JSON file (defaults to demo_data/employee_payroll.json)
    """
    frappe.set_user("Administrator")

    print(f"\n{'='*60}")
    print(f"Creating Payroll Data for Company: {company}")
    print(f"{'='*60}\n")

    # Load payroll data
    if payroll_path is None:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        payroll_path = os.path.join(current_dir, "employee_payroll.json")

    print(f"Loading payroll data from: {payroll_path}")

    import json
    with open(payroll_path, 'r') as f:
        data = json.load(f)

    # Track counts
    counts = {
        "salary_components": 0,
        "salary_structures": 0,
        "structure_assignments": 0,
        "salary_slips": 0,
        "errors": []
    }

    # Step 0: Ensure Fiscal Year exists for salary slip creation
    print("\n" + "="*50)
    print("Step 0: Ensuring Fiscal Year 2025 exists...")
    print("="*50)
    ensure_fiscal_year(company)
    frappe.db.commit()

    # Step 1: Create Salary Components
    print("\n" + "="*50)
    print("Step 1: Creating Salary Components...")
    print("="*50)
    create_salary_components(data.get("salary_components", []), counts)
    frappe.db.commit()

    # Step 2: Create Salary Structures
    print("\n" + "="*50)
    print("Step 2: Creating Salary Structures...")
    print("="*50)
    create_salary_structures(data.get("salary_structures", []), company, counts)
    frappe.db.commit()

    # Step 3: Assign Salary Structures to Employees
    print("\n" + "="*50)
    print("Step 3: Assigning Salary Structures to Employees...")
    print("="*50)
    create_structure_assignments(data.get("employee_assignments", []), company, counts)
    frappe.db.commit()

    # Step 4: Create Salary Slips
    print("\n" + "="*50)
    print("Step 4: Creating Salary Slips...")
    print("="*50)
    create_salary_slips(data.get("employee_assignments", []), company, counts)
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


def create_salary_components(components, counts):
    """Create salary components (earnings and deductions)"""
    for comp in components:
        name = comp.get("name")

        # Check if already exists
        if frappe.db.exists("Salary Component", name):
            print(f"  Already exists: {name}")
            continue

        try:
            doc = frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": name,
                "salary_component_abbr": comp.get("abbr"),
                "type": comp.get("type"),
                "description": comp.get("description", ""),
                "is_tax_applicable": comp.get("is_tax_applicable", 1),
                "depends_on_payment_days": comp.get("depends_on_payment_days", 1)
            })
            doc.insert(ignore_permissions=True)
            counts["salary_components"] += 1
            print(f"  Created: {name} ({comp.get('type')})")
        except Exception as e:
            counts["errors"].append(f"Component {name}: {str(e)[:50]}")
            print(f"  Error creating {name}: {str(e)[:50]}")


def create_salary_structures(structures, company, counts):
    """Create salary structures with earnings and deductions"""
    for struct in structures:
        name = struct.get("name")

        # Check if already exists
        if frappe.db.exists("Salary Structure", name):
            print(f"  Already exists: {name}")
            continue

        try:
            doc = frappe.get_doc({
                "doctype": "Salary Structure",
                "name": name,
                "company": company,
                "is_active": struct.get("is_active", "Yes"),
                "payroll_frequency": struct.get("payroll_frequency", "Monthly"),
                "currency": frappe.db.get_value("Company", company, "default_currency") or "USD"
            })

            # Add earnings
            for earning in struct.get("earnings", []):
                doc.append("earnings", {
                    "salary_component": earning.get("salary_component"),
                    "amount": earning.get("amount", 0),
                    "amount_based_on_formula": 0
                })

            # Add deductions
            for deduction in struct.get("deductions", []):
                doc.append("deductions", {
                    "salary_component": deduction.get("salary_component"),
                    "amount": deduction.get("amount", 0),
                    "amount_based_on_formula": 0
                })

            doc.insert(ignore_permissions=True)
            doc.submit()  # Submit the structure to make it active
            counts["salary_structures"] += 1
            print(f"  Created: {name}")

            # Calculate totals for display
            total_earning = sum(e.get("amount", 0) for e in struct.get("earnings", []))
            total_deduction = sum(d.get("amount", 0) for d in struct.get("deductions", []))
            print(f"    - Earnings: ${total_earning}, Deductions: ${total_deduction}, Net: ${total_earning - total_deduction}")

        except Exception as e:
            counts["errors"].append(f"Structure {name}: {str(e)[:50]}")
            print(f"  Error creating {name}: {str(e)[:50]}")


def create_structure_assignments(assignments, company, counts):
    """Assign salary structures to employees"""
    for assign in assignments:
        emp_id = assign.get("employee_id")
        emp_name = assign.get("employee_name")
        structure = assign.get("salary_structure")
        from_date = assign.get("from_date", "2025-01-01")

        # Verify employee exists
        if not frappe.db.exists("Employee", emp_id):
            print(f"  Employee not found: {emp_id}")
            counts["errors"].append(f"Employee not found: {emp_id}")
            continue

        # Check if assignment already exists
        existing = frappe.db.exists("Salary Structure Assignment", {
            "employee": emp_id,
            "salary_structure": structure
        })

        if existing:
            print(f"  Already assigned: {emp_name} -> {structure}")
            continue

        try:
            doc = frappe.get_doc({
                "doctype": "Salary Structure Assignment",
                "employee": emp_id,
                "salary_structure": structure,
                "from_date": from_date,
                "company": company,
                "base": assign.get("base", 0)
            })
            doc.insert(ignore_permissions=True)
            doc.submit()  # Submit the assignment to make it active
            counts["structure_assignments"] += 1
            print(f"  Assigned: {emp_name} -> {structure} (Base: ${assign.get('base', 0)})")
        except Exception as e:
            counts["errors"].append(f"Assignment {emp_name}: {str(e)[:50]}")
            print(f"  Error assigning {emp_name}: {str(e)[:50]}")


def create_salary_slips(assignments, company, counts):
    """Create salary slips for November 2025"""
    # Payroll period: November 2025
    start_date = "2025-11-01"
    end_date = "2025-11-30"
    posting_date = "2025-11-30"

    print(f"\n  Payroll Period: {start_date} to {end_date}")

    for assign in assignments:
        emp_id = assign.get("employee_id")
        emp_name = assign.get("employee_name")
        structure = assign.get("salary_structure")

        # Check if salary slip already exists
        existing = frappe.db.exists("Salary Slip", {
            "employee": emp_id,
            "start_date": start_date,
            "end_date": end_date
        })

        if existing:
            print(f"  Salary slip exists: {emp_name} ({start_date})")
            continue

        # Verify structure assignment exists
        assignment = frappe.db.exists("Salary Structure Assignment", {
            "employee": emp_id,
            "salary_structure": structure
        })

        if not assignment:
            print(f"  No structure assignment for: {emp_name}")
            counts["errors"].append(f"No assignment for {emp_name}")
            continue

        try:
            # Create salary slip
            doc = frappe.get_doc({
                "doctype": "Salary Slip",
                "employee": emp_id,
                "salary_structure": structure,
                "company": company,
                "posting_date": posting_date,
                "start_date": start_date,
                "end_date": end_date,
                "payroll_frequency": "Monthly"
            })

            # This will auto-calculate based on salary structure
            doc.insert(ignore_permissions=True)

            # Get calculated values
            doc.reload()

            counts["salary_slips"] += 1
            print(f"  Created slip: {emp_name}")
            print(f"    - Gross: ${doc.gross_pay or 0:.2f}, Deductions: ${doc.total_deduction or 0:.2f}, Net: ${doc.net_pay or 0:.2f}")

        except Exception as e:
            counts["errors"].append(f"Salary slip {emp_name}: {str(e)[:80]}")
            print(f"  Error creating slip for {emp_name}: {str(e)[:80]}")


def clear_payroll_data(company="NovaSoft", payroll_path=None):
    """
    Clear existing payroll data
    USE WITH CAUTION - This will delete data!

    Usage: bench --site [sitename] execute hrms.demo_data.payroll_setup.clear_payroll_data
    """
    frappe.set_user("Administrator")

    print(f"\n{'='*60}")
    print(f"Clearing Payroll Data for Company: {company}")
    print(f"{'='*60}\n")

    # Load data to know which records to delete
    if payroll_path is None:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        payroll_path = os.path.join(current_dir, "employee_payroll.json")

    import json
    with open(payroll_path, 'r') as f:
        data = json.load(f)

    deleted = {"slips": 0, "assignments": 0, "structures": 0, "components": 0}

    # Delete salary slips first
    print("Deleting Salary Slips...")
    for assign in data.get("employee_assignments", []):
        emp_id = assign.get("employee_id")
        slips = frappe.get_all("Salary Slip", filters={"employee": emp_id})
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
    for assign in data.get("employee_assignments", []):
        emp_id = assign.get("employee_id")
        assignments = frappe.get_all("Salary Structure Assignment", filters={"employee": emp_id})
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
    for struct in data.get("salary_structures", []):
        name = struct.get("name")
        if frappe.db.exists("Salary Structure", name):
            try:
                doc = frappe.get_doc("Salary Structure", name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("Salary Structure", name, force=True)
                deleted["structures"] += 1
            except Exception as e:
                print(f"  Error deleting structure {name}: {str(e)[:50]}")

    # Delete salary components (only custom ones)
    print("Deleting Custom Salary Components...")
    for comp in data.get("salary_components", []):
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
