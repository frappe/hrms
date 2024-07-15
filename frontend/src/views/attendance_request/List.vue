<template>
	<ion-page>
		<ListView
			doctype="Attendance Request"
			pageTitle="Attendance Request History"
			:tabButtons="TAB_BUTTONS"
			:fields="LEAVE_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import ListView from "@/components/ListView.vue"

const TAB_BUTTONS = ["My Requests", "Team Requests"]
const LEAVE_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"from_date",
	"to_date",
	"reason",
	"shift",
]
const FILTER_CONFIG = [
	{
		fieldname: "shift",
		fieldtype: "Link",
		label: "Shift Type",
		options: "Shift Type",
	},
	{
		fieldname: "reason",
		fieldtype: "Select",
		label: "Reason Type",
		options: "On Duty\nWork From Home",
		// default: "On Duty",
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
