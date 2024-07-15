<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				v-if="formFields.data"
				doctype="Attendance Request"
				v-model="attendanceRequest"
				:isSubmittable="true"
				:fields="formFields.data"
				:id="props.id"
				:showAttachmentView="false"
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

// const dayjs = inject("$dayjs")
const employee = inject("$employee")
// const today = dayjs().format("YYYY-MM-DD")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const attendanceRequest  = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Attendance Request" },
	transform(data) {
		let fields = getFilteredFields(data)
		
		return fields.map((field) => {
			if (field.fieldname === "half_day_date") field.hidden = true
			return field
		})
	},
	onSuccess(_data) {
		//
	},
})
formFields.reload()

// form scripts
watch(
	() => attendanceRequest.value.half_day,
	(half_day) => setHalfDayDate(half_day)
)

watch(
	() => attendanceRequest.value.from_date,
	(from_date) => {
		if (!attendanceRequest.value.to_date) {
			attendanceRequest.value.to_date = from_date
		}
	}
)

watch(
	() => [attendanceRequest.value.from_date, attendanceRequest.value.to_date],
	([from_date, to_date]) => {
		validateDates(from_date, to_date)
		setHalfDayDateRange()
	}
)


// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// ex: employee and other details can be fetched from the session user
	const excludeFields = []

	const employeeFields = [
		"employee",
		"employee_name",
		"company",
	]

	if (!props.id) excludeFields.push(...employeeFields)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function validateDates(from_date, to_date) {
	if (!(from_date && to_date)) return

	const error_message =
		from_date > to_date ? "To Date cannot be before From Date" : ""

	const from_date_field = formFields.data.find(
		(field) => field.fieldname === "from_date"
	)
	from_date_field.error_message = error_message
}


function setHalfDayDate(half_day) {
	const half_day_date = formFields.data.find(
		(field) => field.fieldname === "half_day_date"
	)
	half_day_date.hidden = !half_day
	half_day_date.reqd = half_day

	if (!half_day) return

	if (attendanceRequest.value.from_date === attendanceRequest.value.to_date) {
		attendanceRequest.value.half_day_date = attendanceRequest.value.from_date
	} else {
		setHalfDayDateRange()
	}
}

function setHalfDayDateRange() {
	const half_day_date = formFields.data.find(
		(field) => field.fieldname === "half_day_date"
	)
	half_day_date.minDate = attendanceRequest.value.from_date
	half_day_date.maxDate = attendanceRequest.value.to_date
}

function validateForm() {
	setHalfDayDate(attendanceRequest.value.half_day)
	attendanceRequest.value.employee = employee.data.name
}
</script>
	