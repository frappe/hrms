"""
Expense Claims Setup - Demo Data Generator for HRMS
Creates Expense Claim Types, Employee Advances, and Expense Claims

Usage:
    bench --site [sitename] execute hrms.demo_data.expense_claims_setup.create_expense_claims_data
    Or with custom JSON path:
    bench --site [sitename] execute hrms.demo_data.expense_claims_setup.create_expense_claims_data --kwargs '{"data_path": "/path/to/file.json"}'
"""

import frappe
from frappe.utils import getdate, nowdate


def get_employee_id(employee_name, company="NovaSoft"):
    """Get employee ID from employee name"""
    employee = frappe.db.get_value(
        "Employee",
        {"employee_name": employee_name, "company": company},
        "name"
    )
    return employee


def get_employee_department(employee_id):
    """Get department for an employee"""
    return frappe.db.get_value("Employee", employee_id, "department")


def ensure_fiscal_year(company, year=2025):
    """Ensure a fiscal year exists for the given year"""
    fy_name = f"FY {year}-{year+1}"
    if frappe.db.exists("Fiscal Year", fy_name):
        return fy_name

    # Create fiscal year
    try:
        doc = frappe.get_doc({
            "doctype": "Fiscal Year",
            "year": fy_name,
            "year_start_date": f"{year}-01-01",
            "year_end_date": f"{year}-12-31"
        })
        doc.append("companies", {"company": company})
        doc.insert(ignore_permissions=True)
        print(f"  Created Fiscal Year: {fy_name}")
        return fy_name
    except Exception as e:
        print(f"  Error creating fiscal year: {str(e)[:50]}")
        return None


def create_expense_claims_data(company="NovaSoft", data_path=None):
    """
    Create Expense Claims demo data from JSON file

    :param company: Company name for expense records
    :param data_path: Path to JSON file (defaults to demo_data/expense_claims_data.json)
    """
    frappe.set_user("Administrator")

    print(f"\n{'='*60}")
    print(f"Creating Expense Claims Data for Company: {company}")
    print(f"{'='*60}\n")

    # Ensure fiscal year exists for the data dates (Oct-Nov 2025)
    print("Ensuring Fiscal Year exists...")
    ensure_fiscal_year(company, 2025)
    frappe.db.commit()

    # Load data
    if data_path is None:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "expense_claims_data.json")

    print(f"Loading data from: {data_path}")

    import json
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Track counts
    counts = {
        "expense_types": 0,
        "employee_advances": 0,
        "expense_claims": 0,
        "errors": []
    }

    # Step 1: Create Expense Claim Types
    print("\n" + "="*50)
    print("Step 1: Creating Expense Claim Types...")
    print("="*50)
    create_expense_claim_types(data.get("expense_claim_types", []), company, counts)
    frappe.db.commit()

    # Step 2: Create Employee Advances
    print("\n" + "="*50)
    print("Step 2: Creating Employee Advances...")
    print("="*50)
    create_employee_advances(data.get("employee_advances", []), company, counts)
    frappe.db.commit()

    # Step 3: Ensure all referenced expense types have default accounts
    print("\n" + "="*50)
    print("Step 3: Ensuring default accounts on all referenced expense types...")
    print("="*50)
    ensure_expense_type_accounts(data.get("expense_claims", []), company)
    frappe.db.commit()

    # Step 4: Create Expense Claims
    print("\n" + "="*50)
    print("Step 4: Creating Expense Claims...")
    print("="*50)
    create_expense_claims(data.get("expense_claims", []), company, counts)
    frappe.db.commit()

    # Print summary
    print(f"\n{'='*60}")
    print("Expense Claims Data Creation Complete!")
    print(f"{'='*60}")
    print(f"\n  Expense Claim Types: {counts['expense_types']}")
    print(f"  Employee Advances: {counts['employee_advances']}")
    print(f"  Expense Claims: {counts['expense_claims']}")

    if counts["errors"]:
        print(f"\n  Errors: {len(counts['errors'])}")
        for err in counts["errors"][:10]:
            print(f"    - {err}")

    print(f"\n{'='*60}\n")

    return counts


def get_default_expense_account(company):
    """Get a default expense account for expense claims"""
    # Try common expense accounts in order of preference
    account_names = [
        f"Indirect Expenses - {company[:2].upper()}",
        f"Administrative Expenses - {company[:2].upper()}",
        f"Expenses - {company[:2].upper()}"
    ]
    for acc_name in account_names:
        if frappe.db.exists("Account", acc_name):
            return acc_name
    # Fallback: find any expense account
    account = frappe.db.get_value("Account", {
        "company": company,
        "root_type": "Expense",
        "is_group": 0
    }, "name")
    return account


def create_expense_claim_types(types_list, company, counts):
    """Create expense claim types with default account"""
    default_account = get_default_expense_account(company)
    if not default_account:
        print(f"  WARNING: No default expense account found for {company}")

    for type_data in types_list:
        name = type_data.get("name")

        if frappe.db.exists("Expense Claim Type", name):
            # Update existing type with default account if missing
            existing_doc = frappe.get_doc("Expense Claim Type", name)
            if not existing_doc.accounts:
                existing_doc.append("accounts", {
                    "company": company,
                    "default_account": default_account
                })
                existing_doc.save(ignore_permissions=True)
                print(f"  Updated account for: {name}")
            else:
                print(f"  Already exists: {name}")
            continue

        try:
            doc = frappe.get_doc({
                "doctype": "Expense Claim Type",
                "expense_type": name,
                "description": type_data.get("description", "")
            })
            # Add default account for the company
            if default_account:
                doc.append("accounts", {
                    "company": company,
                    "default_account": default_account
                })
            doc.insert(ignore_permissions=True)
            counts["expense_types"] += 1
            print(f"  Created: {name}")
        except Exception as e:
            counts["errors"].append(f"Type {name}: {str(e)[:50]}")
            print(f"  Error creating {name}: {str(e)[:50]}")


def ensure_expense_type_accounts(claims_list, company):
    """Ensure every expense type referenced by claims has a default account.

    System-default types (Food, Calls, etc.) may exist without a GL account
    configured for this company. This causes 'Set the default account for the
    Expense Claim Type ...' errors when creating claims.
    """
    default_account = get_default_expense_account(company)
    if not default_account:
        print("  WARNING: No default expense account found, skipping")
        return

    # Collect all expense types referenced by claims
    referenced_types = set()
    for claim in claims_list:
        for exp in claim.get("expenses", []):
            referenced_types.add(exp.get("expense_type"))

    for type_name in sorted(referenced_types):
        if not frappe.db.exists("Expense Claim Type", type_name):
            continue

        doc = frappe.get_doc("Expense Claim Type", type_name)
        # Check if this company already has an account entry
        has_account = any(
            row.company == company and row.default_account
            for row in doc.get("accounts", [])
        )
        if not has_account:
            doc.append("accounts", {
                "company": company,
                "default_account": default_account
            })
            doc.save(ignore_permissions=True)
            print(f"  Set default account for: {type_name}")
        else:
            print(f"  Already configured: {type_name}")


def get_advance_account(company):
    """Get or create the employee advance account for the company.

    ERPNext's default account is 'Employee Advances - {abbr}'. We check for
    that first, then fall back to creating one if it doesn't exist.
    """
    abbr = frappe.db.get_value("Company", company, "abbr") or company[:2].upper()

    # Check for ERPNext's default advance account name first
    default_name = f"Employee Advances - {abbr}"
    if frappe.db.exists("Account", default_name):
        # Ensure it has account_type = Receivable (required by Employee Advance doctype)
        current_type = frappe.db.get_value("Account", default_name, "account_type")
        if current_type != "Receivable":
            frappe.db.set_value("Account", default_name, "account_type", "Receivable")
            print(f"  Updated account type to Receivable: {default_name}")
        return default_name

    # Also check the alternate naming convention
    alt_name = f"Advances to Employees - {abbr}"
    if frappe.db.exists("Account", alt_name):
        current_type = frappe.db.get_value("Account", alt_name, "account_type")
        if current_type != "Receivable":
            frappe.db.set_value("Account", alt_name, "account_type", "Receivable")
            print(f"  Updated account type to Receivable: {alt_name}")
        return alt_name

    # Neither exists -- create one under Loans and Advances (Assets)
    parent_account = f"Loans and Advances (Assets) - {abbr}"
    if not frappe.db.exists("Account", parent_account):
        parent_account = frappe.db.get_value("Account", {
            "company": company,
            "root_type": "Asset",
            "is_group": 1
        }, "name")

    if parent_account:
        try:
            doc = frappe.get_doc({
                "doctype": "Account",
                "account_name": "Employee Advances",
                "parent_account": parent_account,
                "company": company,
                "root_type": "Asset",
                "account_type": "Receivable",
                "is_group": 0
            })
            doc.insert(ignore_permissions=True)
            print(f"  Created advance account: {default_name}")
            return default_name
        except Exception as e:
            print(f"  Could not create advance account: {str(e)[:80]}")

    # Final fallback: use Earnest Money if available
    return frappe.db.get_value("Account", f"Earnest Money - {abbr}", "name")


def get_payable_account(company):
    """Get the payable account for expense claims"""
    abbr = frappe.db.get_value("Company", company, "abbr") or company[:2].upper()
    account_names = [
        f"Creditors - {abbr}",
        f"Accounts Payable - {abbr}",
        f"Payroll Payable - {abbr}"
    ]
    for acc_name in account_names:
        if frappe.db.exists("Account", acc_name):
            return acc_name
    return frappe.db.get_value("Account", {
        "company": company,
        "account_type": "Payable",
        "is_group": 0
    }, "name")


def create_employee_advances(advances_list, company, counts):
    """Create employee advances"""
    advance_account = get_advance_account(company)

    for adv in advances_list:
        emp_name = adv.get("employee_name")
        emp_id = get_employee_id(emp_name, company)

        if not emp_id:
            counts["errors"].append(f"Employee not found: {emp_name}")
            print(f"  Employee not found: {emp_name}")
            continue

        # Check if similar advance already exists
        existing = frappe.db.exists("Employee Advance", {
            "employee": emp_id,
            "purpose": adv.get("purpose")
        })

        if existing:
            print(f"  Already exists: Advance for {emp_name}")
            continue

        try:
            currency = frappe.db.get_value("Company", company, "default_currency") or "USD"
            doc = frappe.get_doc({
                "doctype": "Employee Advance",
                "employee": emp_id,
                "posting_date": adv.get("posting_date"),
                "purpose": adv.get("purpose"),
                "advance_amount": adv.get("advance_amount"),
                "company": company,
                "currency": currency,
                "exchange_rate": 1.0,  # Same currency exchange rate
                "advance_account": advance_account
            })
            doc.insert(ignore_permissions=True)

            # Submit if status is Paid
            if adv.get("status") == "Paid":
                doc.submit()
                # Mark as paid
                doc.db_set("status", "Paid")
                doc.db_set("paid_amount", adv.get("advance_amount"))

            counts["employee_advances"] += 1
            print(f"  Created: Advance for {emp_name} - ${adv.get('advance_amount')}")
        except Exception as e:
            counts["errors"].append(f"Advance {emp_name}: {str(e)[:50]}")
            print(f"  Error creating advance for {emp_name}: {str(e)[:50]}")


def get_default_cost_center(company):
    """Get default cost center for the company"""
    abbr = frappe.db.get_value("Company", company, "abbr") or company[:2].upper()
    cost_center = frappe.db.get_value("Cost Center", f"Main - {abbr}", "name")
    if not cost_center:
        cost_center = frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name")
    return cost_center


def create_expense_claims(claims_list, company, counts):
    """Create expense claims with line items"""
    payable_account = get_payable_account(company)
    cost_center = get_default_cost_center(company)

    if not payable_account:
        print("  WARNING: No payable account found - submitted claims may fail")
    if not cost_center:
        print("  WARNING: No cost center found - submitted claims may fail")

    for claim in claims_list:
        emp_name = claim.get("employee_name")
        emp_id = get_employee_id(emp_name, company)

        if not emp_id:
            counts["errors"].append(f"Employee not found: {emp_name}")
            print(f"  Employee not found: {emp_name}")
            continue

        department = get_employee_department(emp_id)
        posting_date = claim.get("posting_date")

        # Calculate total
        total_amount = sum(exp.get("amount", 0) for exp in claim.get("expenses", []))

        # Check if similar claim exists (same employee, date, amount)
        existing = frappe.db.get_value("Expense Claim", {
            "employee": emp_id,
            "posting_date": posting_date,
            "total_claimed_amount": total_amount
        })

        if existing:
            print(f"  Already exists: Claim for {emp_name} on {posting_date}")
            continue

        try:
            doc = frappe.get_doc({
                "doctype": "Expense Claim",
                "employee": emp_id,
                "department": department,
                "posting_date": posting_date,
                "company": company,
                "currency": frappe.db.get_value("Company", company, "default_currency") or "USD",
                "exchange_rate": 1.0
            })

            # Add expense items
            approval_status = claim.get("approval_status", "Draft")
            for exp in claim.get("expenses", []):
                expense_row = {
                    "expense_date": exp.get("expense_date"),
                    "expense_type": exp.get("expense_type"),
                    "description": exp.get("description", ""),
                    "amount": exp.get("amount"),
                    "sanctioned_amount": exp.get("amount")  # Auto-approve amount
                }
                # Add cost center for claims that will be submitted
                if approval_status in ["Approved", "Rejected"] and cost_center:
                    expense_row["cost_center"] = cost_center
                doc.append("expenses", expense_row)

            doc.insert(ignore_permissions=True)

            # Handle status (approval_status already retrieved above)
            status = claim.get("status", "Draft")

            if approval_status == "Approved":
                # Set payable account before submitting
                if payable_account:
                    doc.payable_account = payable_account
                doc.approval_status = "Approved"
                doc.save(ignore_permissions=True)
                doc.submit()

                if status == "Paid":
                    doc.db_set("status", "Paid")
                    doc.db_set("total_amount_reimbursed", total_amount)
                elif status == "Unpaid":
                    doc.db_set("status", "Unpaid")

            elif approval_status == "Rejected":
                # Set payable account before submitting
                if payable_account:
                    doc.payable_account = payable_account
                doc.approval_status = "Rejected"
                doc.save(ignore_permissions=True)
                doc.submit()
                doc.db_set("status", "Rejected")
                if claim.get("rejection_reason"):
                    doc.db_set("remark", claim.get("rejection_reason"))

            counts["expense_claims"] += 1
            print(f"  Created: {emp_name} - ${total_amount:.2f} ({status})")

        except Exception as e:
            counts["errors"].append(f"Claim {emp_name}: {str(e)[:80]}")
            print(f"  Error creating claim for {emp_name}: {str(e)[:80]}")


def clear_expense_claims_data(company="NovaSoft", data_path=None):
    """
    Clear existing expense claims data
    USE WITH CAUTION - This will delete data!

    Usage: bench --site [sitename] execute hrms.demo_data.expense_claims_setup.clear_expense_claims_data
    """
    frappe.set_user("Administrator")

    print(f"\n{'='*60}")
    print(f"Clearing Expense Claims Data for Company: {company}")
    print(f"{'='*60}\n")

    # Load data to know which records to delete
    if data_path is None:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "expense_claims_data.json")

    import json
    with open(data_path, 'r') as f:
        data = json.load(f)

    deleted = {"claims": 0, "advances": 0, "types": 0}

    # Get employee IDs
    employee_names = set()
    for claim in data.get("expense_claims", []):
        employee_names.add(claim.get("employee_name"))
    for adv in data.get("employee_advances", []):
        employee_names.add(adv.get("employee_name"))

    # Delete expense claims
    print("Deleting Expense Claims...")
    for emp_name in employee_names:
        emp_id = get_employee_id(emp_name, company)
        if not emp_id:
            continue

        claims = frappe.get_all("Expense Claim", filters={"employee": emp_id})
        for claim in claims:
            try:
                doc = frappe.get_doc("Expense Claim", claim.name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("Expense Claim", claim.name, force=True)
                deleted["claims"] += 1
            except Exception as e:
                print(f"  Error deleting claim {claim.name}: {str(e)[:50]}")

    # Delete employee advances
    print("Deleting Employee Advances...")
    for emp_name in employee_names:
        emp_id = get_employee_id(emp_name, company)
        if not emp_id:
            continue

        advances = frappe.get_all("Employee Advance", filters={"employee": emp_id})
        for adv in advances:
            try:
                doc = frappe.get_doc("Employee Advance", adv.name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("Employee Advance", adv.name, force=True)
                deleted["advances"] += 1
            except Exception as e:
                print(f"  Error deleting advance {adv.name}: {str(e)[:50]}")

    # Delete expense claim types (only custom ones we created)
    print("Deleting Custom Expense Claim Types...")
    for type_data in data.get("expense_claim_types", []):
        name = type_data.get("name")
        if frappe.db.exists("Expense Claim Type", name):
            try:
                frappe.delete_doc("Expense Claim Type", name, force=True)
                deleted["types"] += 1
            except Exception as e:
                print(f"  Error deleting type {name}: {str(e)[:50]}")

    frappe.db.commit()

    print(f"\n{'='*60}")
    print("Expense Claims Data Deletion Complete!")
    print(f"{'='*60}")
    print(f"  Deleted {deleted['claims']} Expense Claims")
    print(f"  Deleted {deleted['advances']} Employee Advances")
    print(f"  Deleted {deleted['types']} Expense Claim Types")
    print(f"{'='*60}\n")

    return deleted
