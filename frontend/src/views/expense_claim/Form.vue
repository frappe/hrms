<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Expense Claim"
				v-model="expenseClaim"
				:fields="formFields.data"
				:id="props.id"
				:tabbedView="true"
				:tabs="tabs"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { computed, ref, watch, inject } from "vue"

import FormView from "@/components/FormView.vue"

const dayjs = inject("$dayjs")
const today = dayjs().format("YYYY-MM-DD")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const expenseClaim = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Expense Claim" },
	transform(data) {
		let fields = getFilteredFields(data)

		return fields.map((field) => {
			if (field.fieldname === "posting_date") field.default = today

			return field
		})
	},
})
formFields.reload()

const tabs = [
	{
		name: "Expenses",
		lastField: "taxes",
	},
	{
		name: "Advances",
		lastField: "advances",
	},
]

// form scripts

// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// ex: employee and other details can be fetched from the session user
	const excludeFields = ["naming_series", "task", "remark"]

	const employeeFields = ["employee", "employee_name", "department", "company"]

	if (!props.id) excludeFields.push(...employeeFields)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}
</script>
