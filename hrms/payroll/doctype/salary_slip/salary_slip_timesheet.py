# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe.utils import flt

from hrms.payroll.utils import get_salary_component_data


class TimesheetMixin:
	def set_time_sheet(self):
		# caller (get_emp_and_working_day_details) gates this on salary_slip_based_on_timesheet
		self.set("timesheets", [])

		Timesheet = frappe.qb.DocType("Timesheet")
		timesheets = (
			frappe.qb.from_(Timesheet)
			.select(Timesheet.star)
			.where(
				(Timesheet.employee == self.employee)
				& (Timesheet.start_date.between(self.start_date, self.end_date))
				& (
					(Timesheet.status == "Submitted")
					| (Timesheet.status == "Billed")
					| (Timesheet.status == "Partially Billed")
				)
			)
		).run(as_dict=1)

		for data in timesheets:
			self.append("timesheets", {"time_sheet": data.name, "working_hours": data.total_hours})

	def add_timesheet_earning_component(self, timesheet_config):
		self.hour_rate = flt(timesheet_config.hour_rate)
		self.base_hour_rate = flt(self.hour_rate) * flt(self.exchange_rate)
		self.total_working_hours = sum([d.working_hours or 0.0 for d in self.timesheets]) or 0.0
		wages_amount = self.hour_rate * self.total_working_hours

		self.add_earning_for_hourly_wages(self, timesheet_config.timesheet_component, wages_amount)

	def add_earning_for_hourly_wages(self, doc, salary_component, amount):
		row_exists = False
		for row in doc.earnings:
			if row.salary_component == salary_component:
				row.amount = amount
				row_exists = True
				break

		if not row_exists:
			wages_row = get_salary_component_data(salary_component)
			wages_amount = self.hour_rate * self.total_working_hours

			self.update_component_row(
				wages_row,
				wages_amount,
				"earnings",
				default_amount=wages_amount,
			)

	def calculate_total_for_salary_slip_based_on_timesheet(self):
		if self.timesheets:
			self.total_working_hours = 0
			for timesheet in self.timesheets:
				if timesheet.working_hours:
					self.total_working_hours += timesheet.working_hours

		wages_amount = self.total_working_hours * self.hour_rate
		self.base_hour_rate = flt(self.hour_rate) * flt(self.exchange_rate)
		salary_component = frappe.db.get_value(
			"Salary Structure", {"name": self.salary_structure}, "salary_component", cache=True
		)
		if self.earnings:
			for i, earning in enumerate(self.earnings):
				if earning.salary_component == salary_component:
					self.earnings[i].amount = wages_amount
				self.gross_pay += flt(self.earnings[i].amount, earning.precision("amount"))
		self.net_pay = flt(self.gross_pay) - flt(self.total_deduction)
