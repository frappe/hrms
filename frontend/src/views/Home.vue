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
import { inject, markRaw, computed } from "vue"
import { createResource } from "frappe-ui"

import CheckInPanel from "@/components/CheckInPanel.vue"
import QuickLinks from "@/components/QuickLinks.vue"
import BaseLayout from "@/components/BaseLayout.vue"
import RequestPanel from "@/components/RequestPanel.vue"
import AttendanceIcon from "@/components/icons/AttendanceIcon.vue"
import LeaveIcon from "@/components/icons/LeaveIcon.vue"
import ExpenseIcon from "@/components/icons/ExpenseIcon.vue"
import EmployeeAdvanceIcon from "@/components/icons/EmployeeAdvanceIcon.vue"
import SalaryIcon from "@/components/icons/SalaryIcon.vue"

const __ = inject("$translate")

const settings = createResource({
	url: "hrms.api.get_hr_settings",
	auto: true,
})

const quickLinks = computed(() => {
	const links = [
		{
			icon: markRaw(AttendanceIcon),
			title: __("Request Attendance"),
			route: "AttendanceRequestFormView",
		},
		{
			icon: markRaw(LeaveIcon),
			title: __("Request Leave"),
			route: "LeaveApplicationFormView",
		},
		{
			icon: markRaw(SalaryIcon),
			title: __("View Salary Slips"),
			route: "SalarySlipsDashboard",
		},
	]

	if (!settings.data?.hide_accounting_features) {
		links.splice(2, 0,
			{
				icon: markRaw(ExpenseIcon),
				title: __("Claim an Expense"),
				route: "ExpenseClaimFormView",
			},
			{
				icon: markRaw(EmployeeAdvanceIcon),
				title: __("Request an Advance"),
				route: "EmployeeAdvanceFormView",
			},
		)
	}

	return links
})
</script>
