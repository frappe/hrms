"""
Payroll Setup - Demo Data Generator for HRMS
Creates Salary Components, Salary Structures, Structure Assignments, and Salary Slips

Design based on US tech company payroll with weekly schedules.
All configuration is loaded from the JSON file (employee_payroll.json).

Compatible with: Frappe v15.95.0, ERPNext v15.95.0, HRMS v15.55.0

Author: shi-kejian
Version: 4.2.0

Usage:
    bench --site [sitename] execute hrms.demo_data.payroll_setup.create_payroll_data \
        --kwargs '{"company": "NovaSoft", "payroll_path": "/path/to/employee_payroll.json"}'
"""

import frappe
from hrms.demo_data.utils import load_json


def ensure_fiscal_year(company, config):
    """Ensure Fiscal Year exists for the company"""
    fiscal_year = config.get("fiscal_year", "2025")
    year_start = config.get("fiscal_year_start", f"{fiscal_year}-01-01")
    year_end = config.get("fiscal_year_end", f"{fiscal_year}-12-31")

    if not frappe.db.exists("Fiscal Year", fiscal_year):
        doc = frappe.get_doc({
            "doctype": "Fiscal Year",
            "year": fiscal_year,
            "year_start_date": year_start,
            "year_end_date": year_end,
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


def ensure_payroll_period(company, config):
    """Ensure Payroll Period exists for the company"""
    fiscal_year = config.get("fiscal_year", "2025")
    period_name = f"Payroll Period {fiscal_year} - {company}"
    start_date = config.get("payroll_period_start", f"{fiscal_year}-01-01")
    end_date = config.get("payroll_period_end", f"{fiscal_year}-12-31")

    if frappe.db.exists("Payroll Period", period_name):
        print(f"  Payroll Period already exists: {period_name}")
        return period_name

    doc = frappe.get_doc({
        "doctype": "Payroll Period",
        "name": period_name,
        "company": company,
        "start_date": start_date,
        "end_date": end_date
    })
    doc.insert(ignore_permissions=True)
    print(f"  Created Payroll Period: {period_name}")
    return period_name


def ensure_holiday_list(company):
    """Ensure Company has a default Holiday List set.

    In ERPNext/HRMS v15, holiday lists are resolved from:
    1. Employee.holiday_list field (if set on employee)
    2. Company.default_holiday_list field (fallback)

    The company_setup.py script creates the Holiday List and sets it on the Company.
    This function verifies that setup is complete.
    """
    holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")
    if holiday_list:
        print(f"  Holiday List: {holiday_list} (set on Company)")
    else:
        print(f"  WARNING: No default Holiday List set on Company {company}")
        print(f"           Salary slip creation may fail. Run company_setup.py first.")


def ensure_income_tax_slab(company, config, tax_slabs):
    """Create Income Tax Slab with federal tax brackets"""
    fiscal_year = config.get("fiscal_year", "2025")
    slab_name = f"Federal Tax {fiscal_year} - {company}"

    if frappe.db.exists("Income Tax Slab", {"name": slab_name}):
        print(f"  Income Tax Slab already exists: {slab_name}")
        return slab_name

    if not tax_slabs:
        print("  No tax slabs defined, skipping Income Tax Slab creation")
        return None

    doc = frappe.get_doc({
        "doctype": "Income Tax Slab",
        "name": slab_name,
        "company": company,
        "effective_from": config.get("payroll_period_start", f"{fiscal_year}-01-01"),
        "currency": frappe.db.get_value("Company", company, "default_currency") or "USD"
    })

    for slab in tax_slabs:
        doc.append("slabs", {
            "from_amount": slab.get("from_amount", 0),
            "to_amount": slab.get("to_amount", 0),
            "percent_deduction": slab.get("percent_deduction", 0)
        })

    doc.insert(ignore_permissions=True)
    doc.submit()
    print(f"  Created Income Tax Slab: {slab_name} ({len(tax_slabs)} brackets)")
    return slab_name


def delete_default_components(components_to_delete):
    """Delete HRMS default salary components that conflict with our custom ones.

    HRMS v15.55.0 ships with default components (Basic, Leave Encashment, Income Tax)
    that must be removed before creating our custom components.
    """
    if not components_to_delete:
        return

    print("\n  Removing default HRMS salary components...")
    for comp_name in components_to_delete:
        if frappe.db.exists("Salary Component", comp_name):
            try:
                frappe.delete_doc("Salary Component", comp_name, force=True)
                print(f"    Deleted default: {comp_name}")
            except Exception as e:
                print(f"    Error deleting {comp_name}: {str(e)[:80]}")
        else:
            print(f"    Not found (already removed): {comp_name}")


def restore_default_components():
    """Restore HRMS default salary components after clearing payroll data.

    Recreates the default components that ship with HRMS v15.55.0:
    - Leave Encashment (Earning)
    - Basic (Earning)
    - Income Tax (Deduction, is_income_tax_component=1)
    """
    defaults = [
        {"salary_component": "Leave Encashment", "type": "Earning"},
        {"salary_component": "Basic", "type": "Earning"},
        {"salary_component": "Income Tax", "type": "Deduction", "is_income_tax_component": 1},
    ]

    print("\n  Restoring default HRMS salary components...")
    for comp in defaults:
        name = comp["salary_component"]
        if frappe.db.exists("Salary Component", name):
            print(f"    Already exists: {name}")
            continue
        try:
            doc_data = {
                "doctype": "Salary Component",
                "salary_component": name,
                "type": comp["type"],
            }
            if comp.get("is_income_tax_component"):
                doc_data["is_income_tax_component"] = 1
            doc = frappe.get_doc(doc_data)
            doc.insert(ignore_permissions=True)
            print(f"    Restored: {name} ({comp['type']})")
        except Exception as e:
            print(f"    Error restoring {name}: {str(e)[:80]}")


def create_salary_components(salary_components, counts):
    """Create salary components (earnings and deductions) from JSON data"""
    for comp in salary_components:
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

            if comp.get("amount_based_on_formula"):
                doc_data["amount_based_on_formula"] = 1
                doc_data["formula"] = comp.get("formula", "")

            if comp.get("condition"):
                doc_data["condition"] = comp.get("condition")

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


def create_salary_structures(company, salary_structures_data, counts):
    """Create salary structures from JSON data.

    IMPORTANT: Formula and condition must be set on each structure detail row
    (Salary Detail), not just on the Salary Component. The salary slip evaluation
    engine reads these fields from the structure row, not the component.
    See salary_slip.py:1288-1300 (eval_condition_and_formula).
    """
    for struct in salary_structures_data:
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

            for earning in struct.get("earnings", []):
                row_data = {
                    "salary_component": earning.get("salary_component"),
                    "amount_based_on_formula": earning.get("amount_based_on_formula", 0),
                }
                if earning.get("formula"):
                    row_data["formula"] = earning["formula"]
                if earning.get("condition"):
                    row_data["condition"] = earning["condition"]
                doc.append("earnings", row_data)

            for deduction in struct.get("deductions", []):
                row_data = {
                    "salary_component": deduction.get("salary_component"),
                    "amount_based_on_formula": deduction.get("amount_based_on_formula", 0),
                }
                if deduction.get("formula"):
                    row_data["formula"] = deduction["formula"]
                if deduction.get("condition"):
                    row_data["condition"] = deduction["condition"]
                doc.append("deductions", row_data)

            doc.insert(ignore_permissions=True)
            doc.submit()
            counts["salary_structures"] += 1
            print(f"  Created: {name} ({struct.get('payroll_frequency')})")
        except Exception as e:
            counts["errors"].append(f"Structure {name}: {str(e)[:80]}")
            print(f"  Error creating {name}: {str(e)[:80]}")


def create_structure_assignments(company, payroll_data, counts):
    """Assign salary structures to executives and Accounts department employees"""
    config = payroll_data.get("config", {})
    executive_designations = payroll_data.get("executive_designations", [])
    employee_salaries = payroll_data.get("employee_salaries", {})
    default_salary = config.get("default_salary", 75000)

    # Look up Income Tax Slab for linking to assignments
    fiscal_year = config.get("fiscal_year", "2025")
    income_tax_slab = f"Federal Tax {fiscal_year} - {company}"
    if not frappe.db.exists("Income Tax Slab", income_tax_slab):
        income_tax_slab = None

    # Get executives
    all_employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": "Active"},
        fields=["name", "employee_name", "designation", "department", "date_of_joining"]
    )

    executives = [e for e in all_employees if e.designation in executive_designations]
    accounts_staff = [e for e in all_employees if e.department and "Accounts" in e.department]

    # Combine and deduplicate
    target_employees = {e.name: e for e in executives}
    for e in accounts_staff:
        target_employees[e.name] = e

    for emp_id, emp in target_employees.items():
        is_executive = emp.designation in executive_designations
        structure = "Salaried" if is_executive else "Hourly"

        annual_salary = employee_salaries.get(emp.employee_name, default_salary)
        weekly_base = round(annual_salary / 52, 2)

        existing = frappe.db.exists("Salary Structure Assignment", {
            "employee": emp_id,
            "salary_structure": structure
        })

        if existing:
            print(f"  Already assigned: {emp.employee_name} -> {structure}")
            continue

        try:
            assignment_data = {
                "doctype": "Salary Structure Assignment",
                "employee": emp_id,
                "salary_structure": structure,
                "from_date": emp.date_of_joining or "2025-01-01",
                "company": company,
                "base": weekly_base
            }
            if income_tax_slab:
                assignment_data["income_tax_slab"] = income_tax_slab
            doc = frappe.get_doc(assignment_data)
            doc.insert(ignore_permissions=True)
            doc.submit()
            counts["structure_assignments"] += 1
            print(f"  Assigned: {emp.employee_name} -> {structure} (Base: ${weekly_base:.2f}/wk, Annual: ${annual_salary:,})")
        except Exception as e:
            counts["errors"].append(f"Assignment {emp.employee_name}: {str(e)[:80]}")
            print(f"  Error assigning {emp.employee_name}: {str(e)[:80]}")


def get_hi_plan(marital_status, date_of_birth, date_of_joining):
    """Determine Health Insurance plan based on marital status and age.

    - married -> Family
    - single -> Individual
    - widowed or divorced -> age > 50: Individual, otherwise: Family

    Age is calculated relative to the employee's date of joining to keep
    results deterministic regardless of when the script runs.
    """
    from datetime import date

    status = (marital_status or "").strip().lower()

    if status == "married":
        return "Family"
    elif status == "single":
        return "Individual"
    elif status in ("widowed", "divorced"):
        if date_of_birth:
            ref_date = date_of_joining if date_of_joining else date(2025, 1, 1)
            if not isinstance(ref_date, date):
                ref_date = date.fromisoformat(str(ref_date))
            dob = date_of_birth if isinstance(date_of_birth, date) else date.fromisoformat(str(date_of_birth))
            age = ref_date.year - dob.year - ((ref_date.month, ref_date.day) < (dob.month, dob.day))
            return "Individual" if age > 50 else "Family"
        return "Individual"
    else:
        return "Individual"


def create_health_insurance_additional_salaries(company, config, counts):
    """Create recurring Additional Salary records for Health Insurance.

    Health Insurance is a fixed premium set per employee via Additional Salary.
    Plan type is determined by marital status and age:
    - married -> Family ($150.12/wk)
    - single -> Individual ($69.28/wk)
    - widowed/divorced -> age > 50: Individual, age <= 50: Family
    Rates are defined in config: health_insurance_family and health_insurance_individual.
    """
    family_rate = config.get("health_insurance_family", 150.12)
    individual_rate = config.get("health_insurance_individual", 69.28)
    from_date = config.get("payroll_period_start", "2025-01-01")
    to_date = config.get("payroll_period_end", "2025-12-31")
    currency = frappe.db.get_value("Company", company, "default_currency") or "USD"

    assignments = frappe.get_all(
        "Salary Structure Assignment",
        filters={"company": company, "docstatus": 1},
        fields=["employee", "employee_name"]
    )

    for assign in assignments:
        emp_data = frappe.db.get_value(
            "Employee", assign.employee,
            ["marital_status", "date_of_birth", "date_of_joining"],
            as_dict=True
        )

        plan = get_hi_plan(emp_data.marital_status, emp_data.date_of_birth, emp_data.date_of_joining)
        rate = family_rate if plan == "Family" else individual_rate

        existing = frappe.db.exists("Additional Salary", {
            "employee": assign.employee,
            "salary_component": "Health Insurance",
            "docstatus": 1
        })

        if existing:
            print(f"  Already exists: {assign.employee_name} -> HI ({plan})")
            continue

        try:
            # from_date must be >= employee's date_of_joining (Frappe validation)
            doj = emp_data.date_of_joining
            emp_from_date = max(str(doj), from_date) if doj else from_date

            doc = frappe.get_doc({
                "doctype": "Additional Salary",
                "employee": assign.employee,
                "salary_component": "Health Insurance",
                "amount": rate,
                "currency": currency,
                "company": company,
                "is_recurring": 1,
                "from_date": emp_from_date,
                "to_date": to_date,
                "overwrite_salary_structure_amount": 1
            })
            doc.insert(ignore_permissions=True)
            doc.submit()
            counts["additional_salaries"] += 1
            print(f"  Created: {assign.employee_name} -> HI {plan} (${rate:.2f}/wk)")
        except Exception as e:
            counts["errors"].append(f"HI Additional Salary {assign.employee_name}: {str(e)[:80]}")
            print(f"  Error creating HI for {assign.employee_name}: {str(e)[:80]}")


def create_salary_slips(company, config, counts):
    """Create weekly salary slips"""
    week_start = config.get("salary_slip_start", "2025-11-17")
    week_end = config.get("salary_slip_end", "2025-11-23")
    posting_date = week_end

    print(f"\n  Payroll Period: {week_start} to {week_end} (Weekly)")

    assignments = frappe.get_all(
        "Salary Structure Assignment",
        filters={"company": company, "docstatus": 1},
        fields=["employee", "salary_structure", "base"]
    )

    for assign in assignments:
        emp_id = assign.employee
        structure = assign.salary_structure

        emp = frappe.get_doc("Employee", emp_id)

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


def create_payroll_data(company="NovaSoft", payroll_path=None):
    """
    Create Payroll demo data from JSON configuration file.

    :param company: Company name for payroll records
    :param payroll_path: Path to the payroll JSON file (employee_payroll.json)

    Usage:
        bench --site [sitename] execute hrms.demo_data.payroll_setup.create_payroll_data \
            --kwargs '{"company": "NovaSoft", "payroll_path": "/path/to/employee_payroll.json"}'
    """
    frappe.set_user("Administrator")

    if not payroll_path:
        frappe.throw("payroll_path is required. Provide the path to the payroll JSON file.")

    payroll_data = load_json(payroll_path)
    if not payroll_data:
        frappe.throw(f"Failed to load payroll data from: {payroll_path}")

    config = payroll_data.get("config", {})
    salary_components = payroll_data.get("salary_components", [])
    salary_structures = payroll_data.get("salary_structures", [])
    tax_slabs = payroll_data.get("income_tax_slabs", [])
    components_to_delete = payroll_data.get("default_components_to_delete", [])

    print(f"  Loaded {len(salary_components)} salary components, "
          f"{len(salary_structures)} structures, "
          f"{len(tax_slabs)} tax slabs")

    print(f"\n{'='*60}")
    print(f"Creating Payroll Data for Company: {company}")
    print(f"Weekly payroll with US tax structure")
    print(f"{'='*60}\n")

    counts = {
        "salary_components": 0,
        "salary_structures": 0,
        "structure_assignments": 0,
        "additional_salaries": 0,
        "salary_slips": 0,
        "income_tax_slabs": 0,
        "errors": []
    }

    # Step 0: Ensure prerequisites
    print("\n" + "="*50)
    print("Step 0: Ensuring prerequisites...")
    print("="*50)
    ensure_fiscal_year(company, config)
    ensure_payroll_period(company, config)
    ensure_holiday_list(company)
    slab_name = ensure_income_tax_slab(company, config, tax_slabs)
    if slab_name:
        counts["income_tax_slabs"] = 1
    delete_default_components(components_to_delete)
    frappe.db.commit()

    # Step 1: Create Salary Components
    print("\n" + "="*50)
    print("Step 1: Creating Salary Components...")
    print("="*50)
    create_salary_components(salary_components, counts)
    frappe.db.commit()

    # Step 2: Create Salary Structures
    print("\n" + "="*50)
    print("Step 2: Creating Salary Structures...")
    print("="*50)
    create_salary_structures(company, salary_structures, counts)
    frappe.db.commit()

    # Step 3: Assign Salary Structures
    print("\n" + "="*50)
    print("Step 3: Assigning Salary Structures...")
    print("="*50)
    create_structure_assignments(company, payroll_data, counts)
    frappe.db.commit()

    # Step 4: Create Health Insurance Additional Salaries
    print("\n" + "="*50)
    print("Step 4: Creating Health Insurance Additional Salaries...")
    print("="*50)
    create_health_insurance_additional_salaries(company, config, counts)
    frappe.db.commit()

    # Step 5: Create Salary Slips
    print("\n" + "="*50)
    print("Step 5: Creating Salary Slips...")
    print("="*50)
    create_salary_slips(company, config, counts)
    frappe.db.commit()

    # Print summary
    print(f"\n{'='*60}")
    print("Payroll Data Creation Complete!")
    print(f"{'='*60}")
    print(f"\n  Salary Components: {counts['salary_components']}")
    print(f"  Salary Structures: {counts['salary_structures']}")
    print(f"  Structure Assignments: {counts['structure_assignments']}")
    print(f"  Additional Salaries (HI): {counts['additional_salaries']}")
    print(f"  Salary Slips: {counts['salary_slips']}")
    print(f"  Income Tax Slabs: {counts['income_tax_slabs']}")

    if counts["errors"]:
        print(f"\n  Errors: {len(counts['errors'])}")
        for err in counts["errors"][:10]:
            print(f"    - {err}")

    print(f"\n{'='*60}\n")

    return counts


def clear_payroll_data(company="NovaSoft", payroll_path=None):
    """
    Clear existing payroll data.
    USE WITH CAUTION - This will delete data!

    :param company: Company name for payroll records
    :param payroll_path: Path to the payroll JSON file (employee_payroll.json)

    Usage:
        bench --site [sitename] execute hrms.demo_data.payroll_setup.clear_payroll_data \
            --kwargs '{"company": "NovaSoft", "payroll_path": "/path/to/employee_payroll.json"}'
    """
    frappe.set_user("Administrator")

    if not payroll_path:
        frappe.throw("payroll_path is required. Provide the path to the payroll JSON file.")

    payroll_data = load_json(payroll_path)
    if not payroll_data:
        frappe.throw(f"Failed to load payroll data from: {payroll_path}")

    salary_components = payroll_data.get("salary_components", [])
    salary_structures = payroll_data.get("salary_structures", [])
    config = payroll_data.get("config", {})
    fiscal_year = config.get("fiscal_year", "2025")

    print(f"\n{'='*60}")
    print(f"Clearing Payroll Data for Company: {company}")
    print(f"{'='*60}\n")

    deleted = {"slips": 0, "additional_salaries": 0, "assignments": 0, "structures": 0,
              "components": 0, "tax_slabs": 0, "payroll_periods": 0, "fiscal_years": 0}

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

    # Delete Additional Salary records
    print("Deleting Additional Salaries...")
    add_salaries = frappe.get_all("Additional Salary", filters={"company": company})
    for a in add_salaries:
        try:
            doc = frappe.get_doc("Additional Salary", a.name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Additional Salary", a.name, force=True)
            deleted["additional_salaries"] += 1
        except Exception as e:
            print(f"  Error deleting additional salary {a.name}: {str(e)[:50]}")

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

    # Delete salary structures (from JSON)
    print("Deleting Salary Structures...")
    for struct in salary_structures:
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

    # Delete custom salary components (from JSON)
    print("Deleting Custom Salary Components...")
    for comp in salary_components:
        name = comp.get("name")
        if frappe.db.exists("Salary Component", name):
            try:
                frappe.delete_doc("Salary Component", name, force=True)
                deleted["components"] += 1
            except Exception as e:
                print(f"  Error deleting component {name}: {str(e)[:50]}")

    # Delete Income Tax Slab
    print("Deleting Income Tax Slabs...")
    slab_name = f"Federal Tax {fiscal_year} - {company}"
    if frappe.db.exists("Income Tax Slab", slab_name):
        try:
            doc = frappe.get_doc("Income Tax Slab", slab_name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Income Tax Slab", slab_name, force=True)
            deleted["tax_slabs"] += 1
        except Exception as e:
            print(f"  Error deleting tax slab {slab_name}: {str(e)[:50]}")

    # Delete Payroll Period
    print("Deleting Payroll Period...")
    period_name = f"Payroll Period {fiscal_year} - {company}"
    if frappe.db.exists("Payroll Period", period_name):
        try:
            frappe.delete_doc("Payroll Period", period_name, force=True)
            deleted["payroll_periods"] += 1
        except Exception as e:
            print(f"  Error deleting payroll period {period_name}: {str(e)[:50]}")

    # Delete Fiscal Year
    print("Deleting Fiscal Year...")
    if frappe.db.exists("Fiscal Year", fiscal_year):
        try:
            frappe.delete_doc("Fiscal Year", fiscal_year, force=True)
            deleted["fiscal_years"] += 1
        except Exception as e:
            print(f"  Error deleting fiscal year {fiscal_year}: {str(e)[:50]}")

    # Restore HRMS default components
    restore_default_components()

    frappe.db.commit()

    print(f"\n{'='*60}")
    print("Payroll Data Deletion Complete!")
    print(f"{'='*60}")
    print(f"  Deleted {deleted['slips']} Salary Slips")
    print(f"  Deleted {deleted['additional_salaries']} Additional Salaries")
    print(f"  Deleted {deleted['assignments']} Structure Assignments")
    print(f"  Deleted {deleted['structures']} Salary Structures")
    print(f"  Deleted {deleted['components']} Salary Components")
    print(f"  Deleted {deleted['tax_slabs']} Income Tax Slabs")
    print(f"  Deleted {deleted['payroll_periods']} Payroll Periods")
    print(f"  Deleted {deleted['fiscal_years']} Fiscal Years")
    print(f"{'='*60}\n")

    return deleted
