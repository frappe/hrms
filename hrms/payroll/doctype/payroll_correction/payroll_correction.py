import frappe
from frappe.model.document import Document

class PayrollCorrection(Document):

    def validate(self):
        self.validate_days()
        self.insert_breakup_table()

        

    def on_submit(self):
        self.insert_additional_salary()

    def validate_days(self):
        if self.number_of_days_planning_to_reverse and self.salary_slip_id:
            salary_slip = frappe.get_doc("Salary Slip", self.salary_slip_id)
            self.working_days=salary_slip.total_working_days
            self.absent_days=salary_slip.absent_days
            self.lwp_days=salary_slip.leave_without_pay
            self.total_lwp_days=salary_slip.absent_days+salary_slip.leave_without_pay
            
            total_days_reversed = 0

            get_total_days_reversed = frappe.get_list(
                "Payroll Correction",
                filters={
                    "docstatus": 1,
                    "payroll_period": self.payroll_period,
                    "salary_slip_id": self.salary_slip_id,
                    "employee": self.employee,
                },
                fields=["number_of_days_planning_to_reverse"]  
            )

            for days in get_total_days_reversed:
                total_days_reversed += days.number_of_days_planning_to_reverse

            total_lwp_days = self.total_lwp_days or 0
            number_of_days_to_reverse = self.number_of_days_planning_to_reverse or 0

            if total_days_reversed + number_of_days_to_reverse > total_lwp_days:
                frappe.throw(f"You cannot reverse more than the total LWP days ({total_lwp_days}). "
                             f"You have already reversed {total_days_reversed} days for this employee.")

    def insert_breakup_table(self):
        salary_slip = frappe.get_doc("Salary Slip", self.salary_slip_id)
        if not salary_slip:
            frappe.throw("Salary Slip not found.")
        self.set("earning_arrear_component", [])
        self.set("deduction_arrear_component", [])
        total_working_days = salary_slip.total_working_days or 1
        for earning in salary_slip.earnings or []:
            salary_components = frappe.get_all(
                "Salary Component",
                filters={
                    "is_arrear": 1,
                    "mapping_component": earning.salary_component,
                    "disabled": 0,
                    "type": "Earning",
                },
                fields=["name"]
            )
            if not salary_components:
                continue
            one_day_amount = earning.default_amount / total_working_days
            arrear_amount = one_day_amount * self.number_of_days_planning_to_reverse
            for component in salary_components:
                self.append("earning_arrear_component", {
                    "salary_component": component["name"],
                    "amount": arrear_amount
                })
        for deduction in salary_slip.deductions or []:
            salary_components = frappe.get_all(
                "Salary Component",
                filters={
                    "is_arrear": 1,
                    "mapping_component": deduction.salary_component,
                    "disabled": 0,
                    "type": "Deduction",
                },
                fields=["name"]
            )
            if not salary_components:
                continue
            one_day_amount = deduction.default_amount / total_working_days
            arrear_amount = one_day_amount * self.number_of_days_planning_to_reverse
            for component in salary_components:
                self.append("deduction_arrear_component", {
                    "salary_component": component["name"],
                    "amount": arrear_amount
                })

    def insert_additional_salary(self):
        additional_salary_entries = [
            {
                "doctype": "Additional Salary",
                "employee": self.employee,
                "company": self.company,
                "payroll_date": self.additional_salary_date,
                "salary_component": component.salary_component,
                "currency": self.currency,
                "amount": component.amount,
                "payroll_correction": self.name
            }
            for component in (self.earning_arrear_component or []) + (self.deduction_arrear_component or [])
        ]

        for entry in additional_salary_entries:
            doc = frappe.get_doc(entry)
            doc.insert()
            doc.submit()
