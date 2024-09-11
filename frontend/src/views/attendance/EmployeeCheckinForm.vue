<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Employee Checkin"
				v-model="employeeCheckin"
				:fields="formFields.data"
				:id="props.id"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref } from "vue"

import FormView from "@/components/FormView.vue"

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const employeeCheckin = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Employee Checkin" },
	auto: true,
	transform(data) {
		if (props.id) {
			// setFormReadOnly()
			return data
		}
	},
})

// helper functions
function setFormReadOnly() {
	formFields.data.map((field) => (field.read_only = true))
}
</script>
