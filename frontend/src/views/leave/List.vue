<template>
	<ListView
		doctype="Leave Application"
		pageTitle="Leave History"
		:tabButtons="TAB_BUTTONS"
		:fields="LEAVE_FIELDS"
		:filterConfig="FILTER_CONFIG"
	/>
</template>

<script setup>
import ListView from "@/components/ListView.vue"

const TAB_BUTTONS = ["My Leaves", "Team Leaves"]
const LEAVE_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"leave_type",
	"from_date",
	"to_date",
	"total_leave_days",
	"status",
]
const STATUS_FILTER_OPTIONS = ["Open", "Approved", "Rejected"]
const FILTER_CONFIG = [
	{
		fieldname: "status",
		fieldtype: "Select",
		label: "Status",
		options: STATUS_FILTER_OPTIONS,
	},
	{
		fieldname: "leave_type",
		fieldtype: "Link",
		label: "Leave Type",
		options: "Leave Type",
	},
	{
		fieldname: "employee",
		fieldtype: "Link",
		label: "Employee",
		options: "Employee",
	},
	{
		fieldname: "department",
		fieldtype: "Link",
		label: "Department",
		options: "Department",
	},
	{ fieldname: "from_date", fieldtype: "Date", label: "From Date" },
	{ fieldname: "to_date", fieldtype: "Date", label: "To Date" },
]
</script>
