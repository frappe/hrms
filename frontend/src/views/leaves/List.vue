<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<ListView
				doctype="Leave Application"
				:fields="LEAVE_FIELDS"
				pageTitle="Leave History"
				:tabButtons="TAB_BUTTONS"
				:statusFilterOptions="STATUS_FILTER_OPTIONS"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import ListView from "@/components/ListView.vue"

const TAB_BUTTONS = ["My Leaves", "Team Leaves"]
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
const STATUS_FILTER_OPTIONS = ["Open", "Approved", "Rejected", "Cancelled"]
</script>
