// This config holds the fields that should be shown in the request summary action sheet
// TODO: This should be config-driven somehow

export const LEAVE_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "leave_type",
		label: "Leave Type",
		fieldtype: "Link",
	},
	{
		fieldname: "leave_dates",
		label: "Leave Dates",
		fieldtype: "Data",
	},
	{
		fieldname: "half_day",
		label: "Half Day",
		fieldtype: "Check",
	},
	{
		fieldname: "half_day_date",
		label: "Half Day Date",
		fieldtype: "Date",
	},
	{
		fieldname: "total_leave_days",
		label: "Total Leave Days",
		fieldtype: "Float",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
	{
		fieldname: "leave_balance",
		label: "Leave Balance",
		fieldtype: "Float",
	},
	{
		fieldname: "status",
		label: "Status",
		fieldtype: "Select",
	},
	{
		fieldname: "description",
		label: "Reason",
		fieldtype: "Small Text",
	},
]

export const EXPENSE_CLAIM_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "posting_date",
		label: "Posting Date",
		fieldtype: "Date",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
	{
		fieldname: "expenses",
		label: "Expenses",
		fieldtype: "Table",
		componentName: "ExpenseItems",
	},
	{
		fieldname: "total_claimed_amount",
		label: "Total Claimed Amount",
		fieldtype: "Currency",
	},
	{
		fieldname: "total_sanctioned_amount",
		label: "Total Sanctioned Amount",
		fieldtype: "Currency",
	},
	{
		fieldname: "total_taxes_and_charges",
		label: "Total Taxes and Charges",
		fieldtype: "Currency",
	},
	{
		fieldname: "total_advance_amount",
		label: "Total Advance Amount",
		fieldtype: "Currency",
	},
	{
		fieldname: "grand_total",
		label: "Grand Total",
		fieldtype: "Currency",
	},
	{
		fieldname: "status",
		label: "Status",
		fieldtype: "Select",
	},
	{
		fieldname: "approval_status",
		label: "Approval Status",
		fieldtype: "Select",
	},
]

export const ATTENDANCE_REQUEST_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "attendance_dates",
		label: "Attendance Dates",
		fieldtype: "Data",
	},
	{
		fieldname: "total_attendance_days",
		label: "Total Attendance Days",
		fieldtype: "Data",
	},
	{
		fieldname: "include_holidays",
		label: "Include Holidays",
		fieldtype: "Check",
	},
	{
		fieldname: "shift",
		label: "Shift",
		fieldtype: "Link",
	},
	{
		fieldname: "reason",
		label: "Reason",
		fieldtype: "Select",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
]

export const SHIFT_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "shift_type",
		label: "Shift Type",
		fieldtype: "Link",
	},
	{
		fieldname: "shift_timing",
		label: "Shift Timing",
		fieldtype: "Data",
	},
	{
		fieldname: "shift_dates",
		label: "Shift Dates",
		fieldtype: "Data",
	},
	{
		fieldname: "total_shift_days",
		label: "Total Shift Days",
		fieldtype: "Data",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
]

export const SHIFT_REQUEST_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "shift_type",
		label: "Shift Type",
		fieldtype: "Link",
	},
	{
		fieldname: "shift_dates",
		label: "Shift Dates",
		fieldtype: "Data",
	},
	{
		fieldname: "total_shift_days",
		label: "Total Shift Days",
		fieldtype: "Data",
	},
	{
		fieldname: "employee",
		label: "Employee",
		fieldtype: "Link",
	},
	{
		fieldname: "status",
		label: "Status",
		fieldtype: "Select",
	},
]

export const EMPLOYEE_CHECKIN_FIELDS = [
	{
		fieldname: "name",
		label: "ID",
		fieldtype: "Data",
	},
	{
		fieldname: "log_type",
		label: "Log Type",
		fieldtype: "Data",
	},
	{
		fieldname: "date",
		label: "Date",
		fieldtype: "Date",
	},
	{
		fieldname: "formatted_time",
		label: "Time",
		fieldtype: "Time",
	},
	{
		fieldname: "formatted_latitude",
		label: "Latitude",
		fieldtype: "Data",
	},
	{
		fieldname: "formatted_longitude",
		label: "Longitude",
		fieldtype: "Data",
	},
	{
		fieldname: "geolocation",
		label: "Geolocation",
		fieldtype: "geolocation",
	},
]
