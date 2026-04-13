<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Employee Grievance"
				v-model="grievance"
				:fields="formFields.data"
				:id="props.id"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, watch, inject } from "vue"

import FormView from "@/components/FormView.vue"

const __ = inject("$translate")
const sessionEmployee = inject("$employee")
const currEmployee = ref(sessionEmployee.data.name)

const GRIEVANCE_PARTIES = [
	"Company",
	"Department",
	"Employee",
	"Employee Grade",
	"Employee Group",
]

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

const grievance = ref({})

const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Employee Grievance" },
	transform(data) {
		return getFilteredFields(data)
	},
	onSuccess() {
		applyFieldConfig()
	},
})
formFields.reload()

function getFilteredFields(fields) {
	const excludeFields = [
		"naming_series",
		"associated_document_type",
		"associated_document",
	]

	const employeeFields = [
		"raised_by",
		"raised_by_name",
		"company",
		"department",
		"status",
	]

	if (!props.id) excludeFields.push(...employeeFields)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function applyFieldConfig() {
	formFields.data = formFields.data.map((field) => {
		if (field.fieldname === "grievance_against_party") {
			field.documentList = GRIEVANCE_PARTIES.map((party) => ({
				label: party,
				value: party,
			}))
		}
		return field
	})
}

function updateGrievanceAgainstFilter() {
	const grievanceAgainstField = formFields.data?.find(
		(f) => f.fieldname === "grievance_against"
	)
	if (!grievanceAgainstField) return

	if (grievance.value.grievance_against_party === "Employee") {
		grievanceAgainstField.linkFilters = [["Employee", "name", "!=", currEmployee.value]]
	} else {
		grievanceAgainstField.linkFilters = []
	}
}

watch(
	() => grievance.value.grievance_against_party,
	(party) => {
		grievance.value.grievance_against = null
		if (party === "Employee") {
			grievance.value.grievance_against = currEmployee.value
		}
		updateGrievanceAgainstFilter()
	}
)
</script>
