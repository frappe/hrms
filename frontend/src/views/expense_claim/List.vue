<template>
	<ListView
		doctype="Expense Claim"
		pageTitle="Claim History"
		:tabButtons="TAB_BUTTONS"
		:fields="EXPENSE_CLAIM_FIELDS"
		groupBy="`tabExpense Claim`.name"
		:filterConfig="FILTER_CONFIG"
	/>
</template>

<script setup>
import ListView from "@/components/ListView.vue"

const TAB_BUTTONS = ["My Claims", "Team Claims"]
const EXPENSE_CLAIM_FIELDS = [
	"`tabExpense Claim`.name",
	"`tabExpense Claim`.employee",
	"`tabExpense Claim`.employee_name",
	"`tabExpense Claim`.approval_status",
	"`tabExpense Claim`.status",
	"`tabExpense Claim`.expense_approver",
	"`tabExpense Claim`.total_claimed_amount",
	"`tabExpense Claim`.posting_date",
	"`tabExpense Claim`.company",
	"`tabExpense Claim Detail`.expense_type",
	"count(`tabExpense Claim Detail`.expense_type) as total_expenses",
]

const FILTER_CONFIG = [
	{
		fieldname: "approval_status",
		fieldtype: "Select",
		label: "Approval Status",
		options: ["Draft", "Approved", "Rejected"],
	},
	{
		fieldname: "status",
		fieldtype: "Select",
		label: "Status",
		options: ["Draft", "Paid", "Unpaid", "Rejected", "Submitted", "Cancelled"],
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
]
</script>
