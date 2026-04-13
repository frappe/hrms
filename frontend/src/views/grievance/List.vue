<template>
	<ion-page>
		<ListView
			doctype="Employee Grievance"
			:pageTitle="__('My Grievances')"
			:fields="GRIEVANCE_FIELDS"
			:filterConfig="FILTER_CONFIG"
			employeeField="raised_by"
		/>
	</ion-page>
</template>

<script setup>
import { IonPage } from "@ionic/vue"
import ListView from "@/components/ListView.vue"
import { inject } from "vue"

const __ = inject("$translate")

const GRIEVANCE_FIELDS = [
	"name",
	"raised_by",
	"raised_by_name",
	"subject",
	"grievance_against_party",
	"grievance_against",
	"status",
	"date",
]

const FILTER_CONFIG = [
	{
		fieldname: "status",
		fieldtype: "Select",
		label: __("Status"),
		options: ["Open", "Resolved", "Invalid"],
	},
	{
		fieldname: "grievance_against_party",
		fieldtype: "Select",
		label: __("Against Party"),
		options: ["Company", "Department", "Employee", "Employee Grade", "Employee Group"],
	},
]
</script>
