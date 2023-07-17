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
		return data.map((field) => {
			if (field.fieldname === "half_day_date") {
				field.hidden = true
			}
			return field
		})
	}
})
formFields.reload()

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
