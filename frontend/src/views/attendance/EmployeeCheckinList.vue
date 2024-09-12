<template>
	<ion-page>
		<ListView
			doctype="Employee Checkin"
			pageTitle="Employee Checkin History"
			:tabButtons="TAB_BUTTONS"
			:fields="EMPLOYEE_CHECKIN_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import ListView from "@/components/ListView.vue"

const TAB_BUTTONS = ["My Checkins", "Team Checkins"]
const EMPLOYEE_CHECKIN_FIELDS = [
	"name",
	"employee",
	"employee_name",
	"log_type",
	"time",
	"latitude",
	"longitude",
]

const LOG_TYPE_FILTER_OPTIONS = ["", "IN", "OUT"]
const FILTER_CONFIG = [
	{
		fieldname: "employee",
		fieldtype: "Link",
		label: "Employee",
		options: "Employee",
	},
	{
		fieldname: "log_type",
		fieldtype: "Select",
		label: "Log Type",
		options: LOG_TYPE_FILTER_OPTIONS,
	},
	{
		fieldname: "shift",
		fieldtype: "Link",
		label: "Shift",
		options: "Shift Type",
	},
]
</script>
