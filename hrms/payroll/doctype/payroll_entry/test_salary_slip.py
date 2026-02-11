def test_additional_salary_not_repeated():
    employee = create_test_employee()

    additional_salary = frappe.get_doc({
        "doctype": "Additional Salary",
        "employee": employee.name,
        "salary_component": "Bonus",
        "amount": 5000,
        "payroll_date": "2026-01-15"
    }).insert()
    additional_salary.submit()

    # First month
    slip1 = create_salary_slip(employee, "2026-01-01", "2026-01-31")
    slip1.submit()

    # Second month
    slip2 = create_salary_slip(employee, "2026-02-01", "2026-02-28")
    slip2.submit()

    earnings_month2 = [
        d.salary_component for d in slip2.earnings
    ]

    assert "Bonus" not in earnings_month2
