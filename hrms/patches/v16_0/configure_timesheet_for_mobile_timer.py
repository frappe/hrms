"""
Patch: configure_timesheet_for_mobile_timer

Applies two settings required by the HRMS mobile timer feature:
  1. Grants Employee role submit permission on Timesheet
     (so mobile users can submit their own timesheets)
  2. Enables 'ignore_employee_time_overlap' in Projects Settings
     (so the timer can save logs without ERPNext raising OverlapError)
"""

import frappe


def execute():
	# 1. Grant Employee role submit permission on Timesheet
	frappe.db.sql(
		"""
		UPDATE `tabDocPerm`
		SET submit = 1
		WHERE parent = 'Timesheet'
		  AND role = 'Employee'
		  AND permlevel = 0
		  AND submit = 0
		"""
	)

	# 2. Enable ignore_employee_time_overlap in Projects Settings
	frappe.db.set_single_value("Projects Settings", "ignore_employee_time_overlap", 1)

	frappe.db.commit()
