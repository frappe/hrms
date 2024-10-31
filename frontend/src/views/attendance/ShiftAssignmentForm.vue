<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Shift Assignment"
				v-model="shiftAssignment"
				:isSubmittable="true"
				:fields="formFields.data"
				:id="props.id"
				@validateForm="validateForm"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, watch, inject } from "vue"

import FormView from "@/components/FormView.vue"

const employee = inject("$employee")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const shiftAssignment = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Shift Assignment" },
	auto: true,
	transform(data) {
		if (props.id) return data
		return data.filter(
			(field) => !["employee", "employee_name", "status", "company"].includes(field.fieldname)
		)
	},
})

// form scripts
watch(
	() => shiftAssignment.value.employee,
	(employee_id) => {
		if (props.id && employee_id !== employee.data.name) {
			// if employee is not the current user, set form as read only
			setFormReadOnly()
		}
	}
)

watch(
	() => [shiftAssignment.value.start_date, shiftAssignment.value.end_date],
	([start_date, end_date]) => {
		validateDates(start_date, end_date)
	}
)

// helper functions
function setFormReadOnly() {
	formFields.data.map((field) => (field.read_only = true))
}

function validateDates(start_date, end_date) {
	if (!(start_date && end_date)) return

	const error_message = start_date > end_date ? __("End Date cannot be before Start Date") : ""

	const start_date_field = formFields.data.find((field) => field.fieldname === "start_date")
	start_date_field.error_message = error_message
}

function validateForm() {
	shiftAssignment.value.employee = employee.data.name
}
</script>

