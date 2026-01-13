<template>
	<BaseLayout>
		<template #body>
			<div class="flex flex-col items-center my-7 p-4 gap-7">
				<CheckInPanel />
				<QuickLinks :items="quickLinks" :title="__('Quick Links')" />
				<RequestPanel />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { inject, markRaw } from "vue"

import CheckInPanel from "@/components/CheckInPanel.vue"
import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"
import RequestPanel from "@/components/RequestPanel.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import ShiftIcon from "@/components/icons/ShiftIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"
import { createResource } from "frappe-ui"
import { computed } from "vue"

const __ = inject("$translate")

const settings = createResource({
	url: "hrms.api.get_hr_settings",
	auto: true,
})

const quickLinks = computed(() => {
	if (!settings.data) return []

	return [
		settings.data.allow_attendance_request_from_mobile_app && {
			icon: markRaw(AttendanceIcon),
			title: __("Request Attendance"),
			route: "AttendanceRequestFormView",
		},
		settings.data.allow_shift_request_from_mobile_app && {
			icon: markRaw(ShiftIcon),
			title: __("Request a Shift"),
			route: "ShiftRequestFormView",
		},
		settings.data.allow_leave_application_from_mobile_app && {
			icon: markRaw(LeaveIcon),
			title: __("Request Leave"),
			route: "LeaveApplicationFormView",
		},
		settings.data.allow_expense_claim_from_mobile_app && {
			icon: markRaw(ExpenseIcon),
			title: __("Claim an Expense"),
			route: "ExpenseClaimFormView",
		},
		settings.data.allow_employee_advance_from_mobile_app && {
			icon: markRaw(EmployeeAdvanceIcon),
			title: __("Request an Advance"),
			route: "EmployeeAdvanceFormView",
		},
		{
			icon: markRaw(SalaryIcon),
			title: __("View Salary Slips"),
			route: "SalarySlipsDashboard",
		},
	].filter(Boolean)
})

</script>
