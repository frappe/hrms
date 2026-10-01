<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				:key="props.id || 'new'"
				doctype="Compensatory Leave Request"
				v-model="request"
				:isSubmittable="true"
				:fields="fields"
				:id="props.id"
				@validateForm="validateForm"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { computed, inject, ref, watch } from "vue"
import FormView from "@/components/FormView.vue"

const props = defineProps({ id: String })
const employee = inject("$employee")
const request = ref({})

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Compensatory Leave Request" },
	auto: true,
})

const fields = computed(() =>
	(formFields.data || [])
		.filter((field) => {
			if (!props.id && ["employee", "employee_name", "department"].includes(field.fieldname)) {
				return false
			}
			return field.fieldname !== "leave_allocation" || request.value.leave_allocation
		})
		.map((field) => {
			field = { ...field }
			if (
				["employee", "employee_name", "department", "leave_allocation"].includes(field.fieldname)
			) {
				field.read_only = true
			}
			if (field.fieldname === "leave_type") {
				field.reqd = true
				field.linkFilters = { is_compensatory: 1 }
			}
			if (field.fieldname === "half_day_date") {
				field.hidden = !request.value.half_day
				field.reqd = Boolean(request.value.half_day)
				field.minDate = request.value.work_from_date
				field.maxDate = request.value.work_end_date
			}
			if (field.fieldname === "work_end_date") {
				field.minDate = request.value.work_from_date
			}
			return field
		})
)

watch(
	() => request.value.work_from_date,
	(date) => {
		if (!request.value.work_end_date) request.value.work_end_date = date
	}
)

watch(
	() => [request.value.half_day, request.value.work_from_date, request.value.work_end_date],
	([halfDay, fromDate, toDate]) => {
		if (!halfDay || !fromDate || !toDate || fromDate > toDate) return

		const halfDayDate = request.value.half_day_date
		if (fromDate === toDate) {
			request.value.half_day_date = fromDate
		} else if (halfDayDate && (halfDayDate < fromDate || halfDayDate > toDate)) {
			request.value.half_day_date = null
		}
	}
)

function validateForm() {
	if (!props.id) request.value.employee = employee.data.name
	if (!request.value.half_day) request.value.half_day_date = null
}
</script>
