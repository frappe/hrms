import frappe
from frappe import _
from frappe.model.document import Document

class PayrollCorrection(Document):

    def validate(self):
        self.validate_days()
        self.insert_breakup_table()

    def on_submit(self):
        self.insert_additional_salary()

    def validate_days(self):
        if self.days_to_reverse and self.salary_slip_reference:
            salary_slip = frappe.get_doc("Salary Slip", self.salary_slip_reference)
            self.working_days = salary_slip.total_working_days
            self.absent_days = salary_slip.absent_days or 0
            self.lwp_days = salary_slip.leave_without_pay or 0
            self.total_lwp_applied = self.absent_days + self.lwp_days
            payroll_corrections = frappe.get_all(
                "Payroll Correction",
                filters={
                    "docstatus": 1,
                    "payroll_period": self.payroll_period,
                    "salary_slip_reference": self.salary_slip_reference,
                    "employee": self.employee
                },
                fields=["days_to_reverse"]
            )
            total_days_reversed = sum(entry["days_to_reverse"] for entry in payroll_corrections) or 0
            if total_days_reversed + self.days_to_reverse > self.total_lwp_applied:
                frappe.throw(_("You cannot reverse more than the total LWP days {0}. You have already reversed {1} days for this employee.").format(
                    self.total_lwp_applied, total_days_reversed
                ))

    def insert_breakup_table(self):
        salary_slip = frappe.get_doc("Salary Slip", self.salary_slip_reference)
        if not salary_slip:
            frappe.throw(_("Salary Slip not found."))

        self.set("earning_arrear_details", [])
        self.set("deductions_arrear_details", [])

        total_working_days = max(salary_slip.total_working_days, 1)  
        for section, fieldname in [("earnings", "earning_arrear_details"), ("deductions", "deductions_arrear_details")]:
            for item in getattr(salary_slip, section, []):
                components = frappe.get_all(
                    "Salary Component",
                    filters={"is_arrear": 1, "mapping_component": item.salary_component, "disabled": 0,
                             "type": "Earning" if section == "earnings" else "Deduction"},
                    fields=["name"]
                )
                if not components:
                    continue

                one_day_amount = (item.default_amount or 0) / total_working_days
                arrear_amount = one_day_amount * self.days_to_reverse

                for component in components:
                    self.append(fieldname, {"salary_component": component.name, "amount": arrear_amount})

    def insert_additional_salary(self):
        for comp in (self.earning_arrear_details or []) + (self.deductions_arrear_details or []):
            additional_salary = frappe.get_doc({
                "doctype": "Additional Salary",
                "employee": self.employee,
                "company": self.company,
                "payroll_date": self.additional_salary_date,
                "salary_component": comp.salary_component,
                "currency": self.currency,
                "amount": comp.amount,
                "payroll_correction": self.name
            })
            additional_salary.insert()
            additional_salary.submit()
