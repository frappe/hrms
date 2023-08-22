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
		fieldtype: "DateRange",
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
