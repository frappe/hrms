<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				doctype="Timesheet"
				v-model="timesheet"
				:isSubmittable="true"
				:fields="TIMESHEET_FORM_FIELDS"
				:id="props.id"
				:showAttachmentView="true"
				@validateForm="validateForm"
			>
				<template #time_logs="{ isFormReadOnly }">
					<TimeLogsTable
						v-model:timesheet="timesheet"
						:isReadOnly="isFormReadOnly"
						@addLog="addLog"
						@updateLog="updateLog"
						@deleteLog="deleteLog"
					/>
				</template>
			</FormView>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { ref, inject } from "vue"

import FormView from "@/components/FormView.vue"
import TimeLogsTable from "@/components/TimeLogsTable.vue"

const employee = inject("$employee")
const dayjs = inject("$dayjs")

const today = dayjs().format("YYYY-MM-DD")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// Only show time_logs (slot) and note.
// Everything else is auto-filled: employee, company,
// start_date/end_date (derived from logs), total_hours (calculated).
const TIMESHEET_FORM_FIELDS = [
	{ fieldname: "time_logs", fieldtype: "Table", label: "Time Logs" },
	{ fieldname: "note", fieldtype: "Text Editor", label: "Note" },
]

const timesheet = ref({
	employee: employee.data.name,
	employee_name: employee.data.employee_name,
	company: employee.data.company,
	start_date: today,
	end_date: today,
})

function addLog(log) {
	if (!timesheet.value.time_logs) timesheet.value.time_logs = []
	timesheet.value.time_logs.push(log)
	recalculateTotals()
}

function updateLog(log, idx) {
	timesheet.value.time_logs[idx] = log
	recalculateTotals()
}

function deleteLog(idx) {
	timesheet.value.time_logs.splice(idx, 1)
	recalculateTotals()
}

function recalculateTotals() {
	const logs = timesheet.value.time_logs || []

	// total hours
	let total = 0
	logs.forEach((log) => { total += parseFloat(log.hours || 0) })
	timesheet.value.total_hours = parseFloat(total.toFixed(2))

	// start_date = earliest from_time; end_date = latest to_time
	const fromDates = logs.map((l) => l.from_time).filter(Boolean)
	const toDates   = logs.map((l) => l.to_time).filter(Boolean)
	if (fromDates.length) {
		timesheet.value.start_date = dayjs(Math.min(...fromDates.map((d) => new Date(d)))).format("YYYY-MM-DD")
	}
	if (toDates.length) {
		timesheet.value.end_date = dayjs(Math.max(...toDates.map((d) => new Date(d)))).format("YYYY-MM-DD")
	}
}

function validateForm() {}
</script>
