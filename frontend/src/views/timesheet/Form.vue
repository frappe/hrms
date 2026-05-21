<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Timesheet"
				v-model="timesheet"
				:isSubmittable="true"
				:fields="formFields.data"
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
import { createResource } from "frappe-ui"
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

const timesheet = ref({
	employee: employee.data.name,
	employee_name: employee.data.employee_name,
	company: employee.data.company,
	start_date: today,
	end_date: today,
})

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Timesheet" },
	transform(data) {
		return getFilteredFields(data)
	},
})
formFields.reload()

function getFilteredFields(fields) {
	const excludeFields = ["naming_series", "amended_from"]
	const newDocExclude = [
		"employee",
		"employee_name",
		"company",
		"total_hours",
		"total_billable_hours",
		"total_billed_hours",
		"total_costing_amount",
		"total_billable_amount",
		"total_billed_amount",
	]

	if (!props.id) excludeFields.push(...newDocExclude)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

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
	let total = 0
	timesheet.value.time_logs?.forEach((log) => {
		total += parseFloat(log.hours || 0)
	})
	timesheet.value.total_hours = parseFloat(total.toFixed(2))
}

function validateForm() {}
</script>
