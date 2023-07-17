<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView doctype="Leave Application" v-model="leaveApplication" :fields="formFields.data" />
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource, toast } from "frappe-ui"
import { reactive, watch, inject } from "vue";

import FormView from "@/components/FormView.vue"

const dayjs = inject("$dayjs")

// reactive object to store form data
const leaveApplication = reactive({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: {
		doctype: "Leave Application",
	},
	transform(data) {
		let fields = getFilteredFields(data)
		return fields.map((field) => {
			if (field.fieldname === "half_day_date") {
				field.hidden = true
			}
			return field
		})
	}
})
formFields.reload()

function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// ex: employee and other details can be fetched from the session user
	const excludeFields = [
		"naming_series",
		"employee",
		"employee_name",
		"department",
		"company",
		"sb_other_details",
		"salary_slip",
		"letter_head"
	]
	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

// form scripts
watch(
	() => leaveApplication.half_day,
	(half_day) => {
		const half_day_date = formFields.data.find((field) => field.fieldname === "half_day_date")
		half_day_date.hidden = !half_day

		if (leaveApplication.from_date === leaveApplication.to_date)
			leaveApplication.half_day_date = leaveApplication.from_date
		else
			leaveApplication.half_day_date = ""
	},
)

watch(
	() => [leaveApplication.from_date, leaveApplication.to_date],
	([from_date, to_date]) => {
		if (!(from_date && to_date))
			return

		if (from_date > to_date) {
			leaveApplication.from_date = null
		}

		const total_leave_days = dayjs(to_date).diff(dayjs(from_date), "day") + 1
		leaveApplication.total_leave_days = total_leave_days
	},
)

</script>
