<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<FormView
				doctype="Leave Application"
				v-model="leaveApplication"
				:fields="formFields.data"
				@validateForm="validateForm"
			/>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { reactive, watch, inject, onMounted } from "vue";

import FormView from "@/components/FormView.vue"

const dayjs = inject("$dayjs")
const employee = inject("$employee")
// reactive object to store form data
const leaveApplication = reactive({})


// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Leave Application" },
	transform(data) {
		let fields = getFilteredFields(data)
		return fields.map((field) => {
			if (field.fieldname === "half_day_date")
				field.hidden = true

			if (field.fieldname === "posting_date")
				field.default = dayjs().format("YYYY-MM-DD")

			if (field.fieldname === "leave_approver")
				field.reqd = leaveApprovalDetails?.data?.is_mandatory

			return field
		})
	}
})
formFields.reload()

const leaveApprovalDetails = createResource({
	url: "hrms.api.get_leave_approval_details",
	params: { employee: employee.data.name },
})
leaveApprovalDetails.reload()

// form scripts
watch(
	() => leaveApplication.leave_type,
	(leave_type) => setLeaveBalance(leave_type),
)

watch(
	() => leaveApplication.half_day,
	(half_day) => setHalfDayDate(half_day)
)

watch(
	() => (leaveApplication.half_day && leaveApplication.half_day_date),
	() => setTotalLeaveDays(),
)

watch(
	() => [leaveApplication.from_date, leaveApplication.to_date],
	([from_date, to_date]) => {
		validateDates(from_date, to_date)
		setHalfDayDateRange()
		setTotalLeaveDays()
	},
)


// helper functions
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

function validateDates(from_date, to_date) {
	if (!(from_date && to_date))
		return

	const error_message = (
		(from_date > to_date)
		? "From date cannot be greater than To Date"
		: ""
	)

	const from_date_field = formFields.data.find((field) => field.fieldname === "from_date")
	from_date_field.error_message = error_message
}

function setTotalLeaveDays() {
	if (!areValuesSet())
		return

	const leaveDays = createResource({
		url: "hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days",
		params: {
			employee: employee.data.name,
			leave_type: leaveApplication.leave_type,
			from_date: leaveApplication.from_date,
			to_date: leaveApplication.to_date,
			half_day: leaveApplication.half_day,
			half_day_date: leaveApplication.half_day_date,
		},
		onSuccess(data) {
			leaveApplication.total_leave_days = data
		}
	})
	leaveDays.reload()
	setLeaveBalance()
}

function setLeaveBalance() {
	if (!areValuesSet())
		return

	const leaveBalance = createResource({
		url: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
		params: {
			employee: employee.data.name,
			date: leaveApplication.from_date,
			to_date: leaveApplication.to_date,
			leave_type: leaveApplication.leave_type,
			consider_all_leaves_in_the_allocation_period: 1
		},
		onSuccess(data) {
			leaveApplication.leave_balance = data
		}
	})
	leaveBalance.reload()
}

function setHalfDayDate(half_day) {
	const half_day_date = formFields.data.find((field) => field.fieldname === "half_day_date")
	half_day_date.hidden = !half_day

	if (!half_day)
		return

	if (leaveApplication.from_date === leaveApplication.to_date) {
		leaveApplication.half_day_date = leaveApplication.from_date
	} else {
		leaveApplication.half_day_date = ""
		setHalfDayDateRange()
	}
}

function setHalfDayDateRange() {
	const half_day_date = formFields.data.find((field) => field.fieldname === "half_day_date")
	half_day_date.minDate = leaveApplication.from_date
	half_day_date.maxDate = leaveApplication.to_date
}

function setLeaveApprover() {
	leaveApplication.leave_approver = leaveApprovalDetails.data.leave_approver
	leaveApplication.leave_approver_name = leaveApprovalDetails.data.leave_approver_name
}

function areValuesSet() {
	return (
		leaveApplication.from_date
		&& leaveApplication.to_date
		&& leaveApplication.leave_type
	)
}

onMounted(async () => {
	await leaveApprovalDetails.promise
	setLeaveApprover()
	setTotalLeaveDays()
})

function validateForm() {
	setHalfDayDate(leaveApplication.half_day)
}

</script>
