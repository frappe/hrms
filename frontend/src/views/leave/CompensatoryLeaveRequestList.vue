<template>
	<ion-page>
		<ListView
			doctype="Compensatory Leave Request"
			:pageTitle="__('Compensatory Leave Requests')"
			:tabButtons="TAB_BUTTONS"
			:fields="FIELDS"
			:filterConfig="FILTER_CONFIG"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import { inject } from "vue"
import ListView from "@/components/ListView.vue"

const __ = inject("$translate")
const TAB_BUTTONS = ["My Requests", "Team Requests"] // __("My Requests"), __("Team Requests")
const FIELDS = [
	"name",
	"employee",
	"employee_name",
	"leave_type",
	"work_from_date",
	"work_end_date",
	"half_day",
	"docstatus",
]
const FILTER_CONFIG = [
	{ fieldname: "leave_type", fieldtype: "Link", label: __("Leave Type"), options: "Leave Type" },
	{ fieldname: "work_from_date", fieldtype: "Date", label: __("Work From Date") },
	{ fieldname: "work_end_date", fieldtype: "Date", label: __("Work End Date") },
]
</script>
