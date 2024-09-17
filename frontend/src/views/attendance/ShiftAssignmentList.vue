<template>
	<ion-page>
		<ListView
			doctype="Shift Assignment"
			pageTitle="Shift Assignment History"
			:tabButtons="TAB_BUTTONS"
			:fields="SHIFT_ASSIGNMENT_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import ListView from "@/components/ListView.vue"

const TAB_BUTTONS = ["My Shifts", "Team Shifts"]
const SHIFT_ASSIGNMENT_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"shift_type",
	"start_date",
	"end_date",
	"docstatus",
]
const FILTER_CONFIG = [
	{
		fieldname: "shift_type",
		fieldtype: "Link",
		label: "Shift Type",
		options: "Shift Type",
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
	{ fieldname: "start_date", fieldtype: "Date", label: "Start Date" },
	{ fieldname: "end_date", fieldtype: "Date", label: "End Date" },
]
</script>
