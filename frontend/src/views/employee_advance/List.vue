<template>
	<ListView
		doctype="Employee Advance"
		pageTitle="Employee Advances"
		:tabButtons="TAB_BUTTONS"
		:fields="EMPLOYEE_ADVANCE_FIELDS"
		:filterConfig="FILTER_CONFIG"
	/>
</template>

<script setup>
import ListView from "@/components/ListView.vue"

const TAB_BUTTONS = ["My Advances", "Team Advances"]
const EMPLOYEE_ADVANCE_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"status",
	"purpose",
	"advance_amount",
	"paid_amount",
	"claimed_amount",
	"return_amount",
	"posting_date",
	"currency",
]

const STATUS_FILTER_OPTIONS = [
	"Draft",
	"Paid",
	"Unpaid",
	"Claimed",
	"Returned",
	"Partly Claimed and Returned",
	"Cancelled",
]
const FILTER_CONFIG = [
	{
		fieldname: "status",
		fieldtype: "Select",
		label: "Status",
		options: STATUS_FILTER_OPTIONS,
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
	{ fieldname: "posting_date", fieldtype: "Date", label: "Posting Date" },
	{
		fieldname: "advance_amount",
		fieldtype: "Currency",
		label: "Advance Amount",
	},
	{ fieldname: "paid_amount", fieldtype: "Currency", label: "Paid Amount" },
]
</script>
