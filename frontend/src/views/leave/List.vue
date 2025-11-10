<template>
	<ion-page>
		<ListView
			doctype="Leave Application"
			:pageTitle="__('Leave History')"
			:tabButtons="TAB_BUTTONS"
			:fields="LEAVE_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import ListView from "@/components/ListView.vue"
import { inject } from "vue"

const __ = inject("$translate")
const TAB_BUTTONS = ["My Leaves", "Team Leaves"] // __("My Leaves"), __("Team Leaves")
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
const STATUS_FILTER_OPTIONS = ["Open", "Approved", "Rejected"] // __("Open"), __("Approved"), __("Rejected")
const FILTER_CONFIG = [
	{
		fieldname: "status",
		fieldtype: "Select",
		label: __("Status"),
		options: STATUS_FILTER_OPTIONS,
	},
	{
		fieldname: "leave_type",
		fieldtype: "Link",
		label: __("Leave Type"),
		options: "Leave Type",
	},
	{
		fieldname: "employee",
		fieldtype: "Link",
		label: __("Employee"),
		options: "Employee",
	},
	{
		fieldname: "department",
		fieldtype: "Link",
		label: __("Department"),
		options: "Department",
	},
	{ fieldname: "from_date", fieldtype: "Date", label: __("From Date") },
	{ fieldname: "to_date", fieldtype: "Date", label: __("To Date") },
]
</script>
