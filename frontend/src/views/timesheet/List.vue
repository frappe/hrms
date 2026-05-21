<template>
	<ion-page>
		<ListView
			doctype="Timesheet"
			:pageTitle="__('Timesheets')"
			:tabButtons="TAB_BUTTONS"
			:fields="TIMESHEET_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import { inject } from "vue"
import ListView from "@/components/ListView.vue"

const __ = inject("$translate")

const TAB_BUTTONS = ["My Timesheets", "Team Timesheets"]

const TIMESHEET_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"start_date",
	"end_date",
	"total_hours",
	"status",
	"company",
]

const FILTER_CONFIG = [
	{
		fieldname: "status",
		fieldtype: "Select",
		label: "Status",
		options: ["Draft", "Submitted", "Cancelled"],
	},
	{
		fieldname: "employee",
		fieldtype: "Link",
		label: "Employee",
		options: "Employee",
	},
	{ fieldname: "start_date", fieldtype: "Date", label: "Start Date" },
	{ fieldname: "end_date", fieldtype: "Date", label: "End Date" },
]
</script>
