<template>
	<ion-page>
		<ListView
			doctype="Employee Checkin"
			pageTitle="Employee Checkin History"
			:fields="EMPLOYEE_CHECKIN_FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import ListView from "@/components/ListView.vue"

const EMPLOYEE_CHECKIN_FIELDS = ["name", "log_type", "time", "latitude", "longitude"]

const LOG_TYPE_FILTER_OPTIONS = ["", "IN", "OUT"]
const FILTER_CONFIG = [
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
