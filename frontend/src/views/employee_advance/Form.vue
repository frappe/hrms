<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Employee Advance"
				v-model="employeeAdvance"
				:isSubmittable="true"
				:fields="formFields.data"
				:id="props.id"
				:showAttachmentView="true"
				@validateForm="validateForm"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, inject, watch } from "vue"

import FormView from "@/components/FormView.vue"
import { useCurrencyConversion } from "@/composables/useCurrencyConversion"

const employee = inject("$employee")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// object to store form data
const employeeAdvance = ref({
	employee: employee.data.name,
	employee_name: employee.data.employee_name,
	company: employee.data.company,
	department: employee.data.department,
})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Employee Advance" },
	transform(data) {
		const fields = getFilteredFields(data)
		return applyFilters(fields)
	},
})
formFields.reload()

useCurrencyConversion(
	formFields,
	employeeAdvance,
	["paid_amount"]
)

// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// eg: employee and other details can be fetched from the session user
	const excludeFields = ["naming_series", "base_paid_amount"]
	const extraFields = [
		"employee",
		"employee_name",
		"department",
		"company",
		"more_info_section",
		"pending_amount",
	]

	if (!props.id) excludeFields.push(...extraFields)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function applyFilters(fields) {
	return fields.map((field) => {
		if (field.fieldname === "advance_account") {
			if (!employeeAdvance.value.currency) return field

			field.linkFilters = {
				root_type: "Asset",
				is_group: 0,
				account_type: "Receivable",
				account_currency: employeeAdvance.value.currency,
				company: employeeAdvance.value.company,
			}
		}

		return field
	})
}

watch(
	() => employeeAdvance.value.currency,
	() => {
		applyFilters(formFields.data)
	}
)

function validateForm() {}
</script>